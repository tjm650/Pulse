import { supabase } from "@/services/supabase";

const PROFILE_FIELDS =
  "id,username,first_name,last_name,bio,profession,profile_image_path,cover_image_path,verified,is_online,last_seen";

async function requireUserId() {
  const { data, error } = await supabase.auth.getUser();
  if (error || !data?.user?.id) {
    throw new Error("Your Supabase session has expired. Please sign in again.");
  }
  return data.user.id;
}

async function getProfiles(userIds = []) {
  const ids = [...new Set(userIds.filter(Boolean))];
  if (!ids.length) return new Map();

  const { data, error } = await supabase
    .from("profiles")
    .select(PROFILE_FIELDS)
    .in("id", ids);

  if (error) throw error;
  return new Map((data || []).map((profile) => [profile.id, profile]));
}

async function getSignedImageUrl(path) {
  if (!path) return null;
  const { data, error } = await supabase.storage
    .from("pulse-message-media")
    .createSignedUrl(path, 60 * 60);
  if (error) {
    console.warn("[Pulse Realtime] Could not sign message image:", error.message);
    return null;
  }
  return data?.signedUrl || null;
}

function decodeBase64(value) {
  const base64 = String(value || "")
    .replace(/^data:[^,]*;base64,/i, "")
    .replace(/\s/g, "");
  if (!base64 || base64.length % 4 !== 0 || !/^[A-Za-z0-9+/]*={0,2}$/.test(base64)) {
    throw new Error("The selected image is not valid base64 data.");
  }

  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  const padding = base64.endsWith("==") ? 2 : base64.endsWith("=") ? 1 : 0;
  const bytes = new Uint8Array((base64.length * 3) / 4 - padding);
  let buffer = 0;
  let bits = 0;
  let offset = 0;

  for (const character of base64.replace(/=+$/, "")) {
    buffer = (buffer << 6) | alphabet.indexOf(character);
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      bytes[offset++] = (buffer >> bits) & 0xff;
    }
  }
  return bytes;
}

function getImageContentType(filename) {
  const extension = String(filename || "").split(".").pop().toLowerCase();
  const types = {
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    png: "image/png",
    webp: "image/webp",
    gif: "image/gif",
  };
  const contentType = types[extension];
  if (!contentType) {
    throw new Error("Only JPG, PNG, WEBP and GIF images are supported.");
  }
  return contentType;
}

async function mapDirectMessage(row, profiles, currentUserId) {
  return {
    ...row,
    created: row.created_at,
    image: await getSignedImageUrl(row.image_path),
    sender: profiles.get(row.sender_id) || { id: row.sender_id },
    is_me: row.sender_id === currentUserId,
  };
}

function mapGroupMessage(row, profiles, currentUserId) {
  return {
    ...row,
    created: row.created_at,
    sender: profiles.get(row.sender_id) || { id: row.sender_id },
    is_me: row.sender_id === currentUserId,
  };
}

export async function getDirectMessages(connectionId, page = 0) {
  const userId = await requireUserId();
  const { data: connection, error: connectionError } = await supabase
    .from("connections")
    .select("id,sender_id,receiver_id,accepted")
    .eq("id", connectionId)
    .eq("accepted", true)
    .maybeSingle();

  if (connectionError) throw connectionError;
  if (!connection || ![connection.sender_id, connection.receiver_id].includes(userId)) {
    throw new Error("This conversation is unavailable.");
  }

  const otherUserId =
    connection.sender_id === userId ? connection.receiver_id : connection.sender_id;
  const pageSize = 20;
  const start = Math.max(0, Number(page) || 0) * pageSize;
  const { data: rows, error } = await supabase
    .from("direct_messages")
    .select("id,connection_id,sender_id,image_path,red,description,created_at")
    .eq("connection_id", connectionId)
    .order("created_at", { ascending: false })
    .range(start, start + pageSize);

  if (error) throw error;
  const profiles = await getProfiles([
    userId,
    otherUserId,
    ...(rows || []).map((row) => row.sender_id),
  ]);
  const messages = await Promise.all(
    (rows || []).slice(0, pageSize).map((row) =>
      mapDirectMessage(row, profiles, userId)
    )
  );

  return {
    messages,
    next: (rows || []).length > pageSize ? Number(page) + 1 : null,
    connect: profiles.get(otherUserId) || { id: otherUserId },
  };
}

export async function getDirectConnections() {
  const userId = await requireUserId();
  const { data: connections, error } = await supabase
    .from("connections")
    .select("id,sender_id,receiver_id,accepted,updated_at")
    .eq("accepted", true)
    .or(`sender_id.eq.${userId},receiver_id.eq.${userId}`)
    .order("updated_at", { ascending: false });

  if (error) throw error;
  if (!connections?.length) return [];

  const otherIds = connections.map((connection) =>
    connection.sender_id === userId ? connection.receiver_id : connection.sender_id
  );
  const profiles = await getProfiles(otherIds);
  const { data: latestMessages, error: messageError } = await supabase
    .from("direct_messages")
    .select("id,connection_id,sender_id,description,image_path,red,created_at")
    .in("connection_id", connections.map((connection) => connection.id))
    .order("created_at", { ascending: false });

  if (messageError) throw messageError;
  const latestByConnection = new Map();
  for (const message of latestMessages || []) {
    if (!latestByConnection.has(message.connection_id)) {
      latestByConnection.set(message.connection_id, message);
    }
  }

  return Promise.all(connections.map(async (connection) => {
    const otherId =
      connection.sender_id === userId ? connection.receiver_id : connection.sender_id;
    const connect = profiles.get(otherId) || { id: otherId };
    const latest = latestByConnection.get(connection.id);
    return {
      id: connection.id,
      connectionId: connection.id,
      connect,
      preview: latest?.description || "",
      preview_red: latest?.red ?? false,
      image: await getSignedImageUrl(latest?.image_path),
      updated: latest?.created_at || connection.updated_at,
    };
  }));
}

export async function sendDirectMessage(details) {
  const userId = await requireUserId();
  if (details?.image) {
    throw new Error("Image messages need the secured Supabase Storage upload path, which is being configured separately. Text messages are available now.");
  }
  const message = String(details?.message || "");
  if ((!message.trim() && !details?.image) || message.length > 10000) {
    throw new Error("Enter a message or attach an image. Text is limited to 10,000 characters.");
  }

  let imagePath = null;
  if (details?.image) {
    const filename = String(details.image.fileName || "message-image.jpg")
      .split(/[\\/]/)
      .pop()
      .replace(/[^A-Za-z0-9._-]/g, "_");
    const contentType = getImageContentType(filename);
    const bytes = decodeBase64(details.image.base64);
    if (bytes.byteLength > 5 * 1024 * 1024) {
      throw new Error("Message images must be 5 MB or smaller.");
    }

    imagePath = `${details.connectionId}/${userId}/${Date.now()}-${filename}`;
    const { error: uploadError } = await supabase.storage
      .from("pulse-message-media")
      .upload(imagePath, bytes, {
        contentType,
        cacheControl: "3600",
        upsert: false,
      });
    if (uploadError) throw uploadError;
  }

  const { data, error } = await supabase
    .from("direct_messages")
    .insert({
      connection_id: details.connectionId,
      sender_id: userId,
      description: message,
      image_path: imagePath,
    })
    .select("id,connection_id,sender_id,image_path,red,description,created_at")
    .single();

  if (error) {
    if (imagePath) {
      await supabase.storage.from("pulse-message-media").remove([imagePath]);
    }
    throw error;
  }
  return data;
}

export async function markDirectMessagesRead(connectionId) {
  const userId = await requireUserId();
  const { error } = await supabase
    .from("direct_messages")
    .update({ red: true })
    .eq("connection_id", connectionId)
    .neq("sender_id", userId)
    .eq("red", false);

  if (error) throw error;
}

export async function getGroupConnections() {
  const userId = await requireUserId();
  const { data: groups, error } = await supabase
    .from("group_connections")
    .select("id,name,creator_id,updated_at,created_at")
    .order("updated_at", { ascending: false });

  if (error) throw error;
  if (!groups?.length) return [];

  const groupIds = groups.map((group) => group.id);
  const { data: memberships, error: memberError } = await supabase
    .from("group_members")
    .select("group_id,user_id")
    .in("group_id", groupIds);
  if (memberError) throw memberError;

  const { data: messages, error: messagesError } = await supabase
    .from("group_messages")
    .select("id,connection_id,sender_id,text,created_at")
    .in("connection_id", groupIds)
    .order("created_at", { ascending: false });
  if (messagesError) throw messagesError;

  const memberIds = [
    ...groups.map((group) => group.creator_id),
    ...(memberships || []).map((member) => member.user_id),
    ...(messages || []).map((message) => message.sender_id),
  ];
  const profiles = await getProfiles(memberIds);
  const latestByGroup = new Map();
  for (const message of messages || []) {
    if (!latestByGroup.has(message.connection_id)) {
      latestByGroup.set(message.connection_id, message);
    }
  }

  return groups.map((group) => {
    const memberIdsForGroup = new Set([
      group.creator_id,
      ...(memberships || [])
        .filter((member) => member.group_id === group.id)
        .map((member) => member.user_id),
    ]);
    const latest = latestByGroup.get(group.id);
    return {
      id: group.id,
      name: group.name,
      updated: latest?.created_at || group.updated_at,
      preview: latest?.text || "No messages yet",
      group_chats_sender: latest
        ? profiles.get(latest.sender_id) || { id: latest.sender_id }
        : null,
      grpconnect: profiles.get(group.creator_id) || { id: group.creator_id },
      members: [...memberIdsForGroup].map((id) => profiles.get(id) || { id }),
      is_member: memberIdsForGroup.has(userId),
    };
  });
}

export async function getGroupMessages(groupId, page = 0) {
  const userId = await requireUserId();
  const { data: group, error: groupError } = await supabase
    .from("group_connections")
    .select("id,name,creator_id")
    .eq("id", groupId)
    .maybeSingle();

  if (groupError) throw groupError;
  if (!group) throw new Error("This group is unavailable.");

  const { data: memberships, error: memberError } = await supabase
    .from("group_members")
    .select("user_id")
    .eq("group_id", groupId);
  if (memberError) throw memberError;

  const memberIds = new Set([
    group.creator_id,
    ...(memberships || []).map((member) => member.user_id),
  ]);
  if (!memberIds.has(userId)) throw new Error("You are not a member of this group.");

  const pageSize = 20;
  const start = Math.max(0, Number(page) || 0) * pageSize;
  const { data: rows, error } = await supabase
    .from("group_messages")
    .select("id,connection_id,sender_id,text,created_at")
    .eq("connection_id", groupId)
    .order("created_at", { ascending: false })
    .range(start, start + pageSize);
  if (error) throw error;

  const profiles = await getProfiles([
    ...memberIds,
    ...(rows || []).map((row) => row.sender_id),
  ]);
  return {
    grp_messages: (rows || []).slice(0, pageSize).map((row) =>
      mapGroupMessage(row, profiles, userId)
    ),
    grpconnect: [...memberIds].map((id) => profiles.get(id) || { id }),
  };
}

export async function sendGroupMessage(groupId, text) {
  const userId = await requireUserId();
  const message = String(text || "");
  if (!message.trim() || message.length > 10000) {
    throw new Error("Enter a group message of up to 10,000 characters.");
  }

  const { data, error } = await supabase
    .from("group_messages")
    .insert({
      connection_id: groupId,
      sender_id: userId,
      text: message,
    })
    .select("id,connection_id,sender_id,text,created_at")
    .single();

  if (error) throw error;
  return data;
}

export async function getUserNotifications(unreadOnly = false) {
  const userId = await requireUserId();
  let query = supabase
    .from("user_notifications")
    .select("id,recipient_id,sender_id,notif_type,description,related_id,is_read,content_type,extra_data,created_at")
    .eq("recipient_id", userId)
    .order("created_at", { ascending: false })
    .limit(100);

  if (unreadOnly) query = query.eq("is_read", false);
  const { data: rows, error } = await query;
  if (error) throw error;

  const profiles = await getProfiles((rows || []).map((row) => row.sender_id));
  return (rows || []).map((row) => ({
    ...row,
    created: row.created_at,
    sender: profiles.get(row.sender_id) || { id: row.sender_id },
  }));
}

export async function markUserNotificationRead(notificationId) {
  const { error } = await supabase
    .from("user_notifications")
    .update({ is_read: true })
    .eq("id", notificationId);
  if (error) throw error;
}

export function subscribePulseRealtime({
  userId,
  onDirectMessage,
  onGroupMessage,
  onUserNotification,
  onConnectionChange,
  onGroupChange,
}) {
  const channel = supabase
    .channel(`pulse-realtime-${userId}`)
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "direct_messages" },
      (payload) => onDirectMessage?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "group_messages" },
      (payload) => onGroupMessage?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "user_notifications" },
      (payload) => onUserNotification?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "notifications" },
      (payload) => onUserNotification?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "connections" },
      (payload) => onConnectionChange?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "group_connections" },
      (payload) => onGroupChange?.(payload)
    )
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "group_members" },
      (payload) => onGroupChange?.(payload)
    )
    .subscribe();

  return channel;
}
