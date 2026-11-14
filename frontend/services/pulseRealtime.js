import { supabase } from "@/services/supabase";

const PROFILE_FIELDS =
  "id,username,first_name,last_name,bio,profession,prof_initial,program,service_name,location,website,directory_status1,profile_image_path,cover_image_path,verified";

const typingChannels = new Map();
const typingTimeouts = new Map();

function getTypingTopic(conversationId, isGroup = false) {
  const id = Number(conversationId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new Error("A valid conversation is required for typing indicators.");
  }
  return `pulse:${isGroup ? "group" : "dm"}:${id}`;
}

export async function subscribeTyping(conversationId, isGroup, onTyping) {
  const userId = await requireUserId();
  const topic = getTypingTopic(conversationId, isGroup);
  const existing = typingChannels.get(topic);
  if (existing) {
    await supabase.removeChannel(existing);
  }

  const channel = supabase.channel(topic, {
    config: {
      private: true,
      broadcast: { ack: false, self: false },
    },
  });

  channel.on("broadcast", { event: "typing" }, ({ payload }) => {
    if (!payload?.userId || payload.userId === userId) return;
    const previous = typingTimeouts.get(topic);
    if (previous) clearTimeout(previous);

    if (!payload.typing) {
      typingTimeouts.delete(topic);
      onTyping?.(null);
      return;
    }

    onTyping?.({
      userId: payload.userId,
      username: payload.username || "Someone",
    });

    const timeout = setTimeout(() => {
      typingTimeouts.delete(topic);
      onTyping?.(null);
    }, 3500);
    typingTimeouts.set(topic, timeout);
  });

  channel.subscribe((status, error) => {
    if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
      console.warn("[Pulse Realtime] Typing channel unavailable:", error?.message || status);
    }
  });

  typingChannels.set(topic, channel);
  return channel;
}

export async function publishTyping(conversationId, isGroup, typing, username) {
  await requireUserId();
  const topic = getTypingTopic(conversationId, isGroup);
  const channel = typingChannels.get(topic);
  if (!channel) return { success: false, reason: "typing_channel_not_ready" };

  const { data } = await supabase.auth.getUser();
  return channel.send({
    type: "broadcast",
    event: "typing",
    payload: {
      userId: data.user.id,
      username: String(username || "Someone").slice(0, 80),
      typing: Boolean(typing),
    },
  });
}

export async function unsubscribeTyping(conversationId, isGroup = false) {
  const topic = getTypingTopic(conversationId, isGroup);
  const timeout = typingTimeouts.get(topic);
  if (timeout) clearTimeout(timeout);
  typingTimeouts.delete(topic);
  const channel = typingChannels.get(topic);
  typingChannels.delete(topic);
  if (channel) await supabase.removeChannel(channel);
}

export async function unsubscribeAllTyping() {
  const channels = [...typingChannels.values()];
  typingChannels.clear();
  for (const timeout of typingTimeouts.values()) clearTimeout(timeout);
  typingTimeouts.clear();
  if (channels.length) await Promise.all(channels.map((channel) => supabase.removeChannel(channel)));
}

async function requireUserId() {
  if (!supabase) {
    throw new Error("Supabase is not configured in this development environment. Messaging and Realtime features are unavailable.");
  }
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
  return new Map(
    (data || []).map((profile) => {
      const name = [profile.first_name, profile.last_name]
        .map((part) => String(part || "").trim())
        .filter(Boolean)
        .join(" ") || profile.username || "";
      return [
        profile.id,
        {
          ...profile,
          name,
          full_name: name,
          image: profile.profile_image_path || null,
          profile_image: profile.profile_image_path || null,
        },
      ];
    })
  );
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

export async function getConnectionRequests() {
  const userId = await requireUserId();
  const { data: requests, error } = await supabase
    .from("connections")
    .select("id,sender_id,receiver_id,accepted,created_at")
    .eq("receiver_id", userId)
    .eq("accepted", false)
    .order("created_at", { ascending: false });

  if (error) throw error;
  const profiles = await getProfiles([
    userId,
    ...(requests || []).map((request) => request.sender_id),
  ]);
  return (requests || []).map((request) => ({
    ...request,
    sender: profiles.get(request.sender_id) || { id: request.sender_id },
    receiver: profiles.get(request.receiver_id) || { id: request.receiver_id },
  }));
}

async function findConnectionForUsername(username) {
  const userId = await requireUserId();
  const { data: target, error: profileError } = await supabase
    .from("profiles")
    .select("id,username")
    .eq("username", username)
    .maybeSingle();

  if (profileError) throw profileError;
  if (!target || target.id === userId) {
    throw new Error("That user is unavailable for a connection request.");
  }

  const { data: connections, error } = await supabase
    .from("connections")
    .select("id,sender_id,receiver_id,accepted,created_at")
    .or(`sender_id.eq.${userId},receiver_id.eq.${userId}`);

  if (error) throw error;
  const existing = (connections || []).find(
    (connection) =>
      (connection.sender_id === userId && connection.receiver_id === target.id) ||
      (connection.receiver_id === userId && connection.sender_id === target.id)
  );
  return { userId, target, existing };
}

export async function requestOrAcceptConnection(username) {
  const { userId, target, existing } = await findConnectionForUsername(username);
  if (existing?.accepted) return { status: "connected", connection: existing };

  if (existing && existing.receiver_id === userId) {
    const { data, error } = await supabase
      .from("connections")
      .update({ accepted: true })
      .eq("id", existing.id)
      .select("id,sender_id,receiver_id,accepted,created_at")
      .single();
    if (error) throw error;
    return { status: "connected", connection: data };
  }

  if (existing) return { status: "pending_them", connection: existing };

  const { data, error } = await supabase
    .from("connections")
    .insert({
      sender_id: userId,
      receiver_id: target.id,
      accepted: false,
    })
    .select("id,sender_id,receiver_id,accepted,created_at")
    .single();

  if (error) throw error;
  return { status: "pending_them", connection: data };
}

export async function acceptConnectionRequest(username) {
  const { userId, target, existing } = await findConnectionForUsername(username);
  if (!existing || existing.accepted || existing.receiver_id !== userId) {
    throw new Error("There is no pending request from this user to accept.");
  }
  const { data, error } = await supabase
    .from("connections")
    .update({ accepted: true })
    .eq("id", existing.id)
    .select("id,sender_id,receiver_id,accepted,created_at")
    .single();
  if (error) throw error;
  return { status: "connected", connection: data, target };
}

export async function deleteConnectionRequest(username) {
  const { userId, existing } = await findConnectionForUsername(username);
  if (!existing || existing.accepted) {
    throw new Error("There is no pending connection request to remove.");
  }
  const { error } = await supabase.from("connections").delete().eq("id", existing.id);
  if (error) throw error;
  return { status: "not-connected", connection: existing };
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

  const items = await Promise.all(connections.map(async (connection) => {
    const otherId =
      connection.sender_id === userId ? connection.receiver_id : connection.sender_id;
    const connect = profiles.get(otherId) || { id: otherId };
    const latest = latestByConnection.get(connection.id);
    return {
      id: connection.id,
      connectionId: connection.id,
      connect,
      sender: latest?.sender_id || null,
      is_sender: latest?.sender_id || null,
      preview: latest?.description || (latest?.image_path ? "Photo" : ""),
      preview_red: latest?.red ?? false,
      image: await getSignedImageUrl(latest?.image_path),
      updated: latest?.created_at || connection.updated_at,
    };
  }));
  return items.sort((a, b) => new Date(b.updated || 0) - new Date(a.updated || 0));
}

export async function sendDirectMessage(details) {
  const userId = await requireUserId();
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
    const encodedImage = String(details.image.base64 || "");
    if (encodedImage.length > 7100000) {
      throw new Error("Message images must be 5 MB or smaller.");
    }
    const bytes = decodeBase64(encodedImage);
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

  const items = groups.map((group) => {
    const memberIdsForGroup = new Set([
      group.creator_id,
      ...(memberships || [])
        .filter((member) => member.group_id === group.id)
        .map((member) => member.user_id),
    ]);
    const latest = latestByGroup.get(group.id);
    const creator = profiles.get(group.creator_id) || { id: group.creator_id };
    return {
      id: group.id,
      name: group.name,
      updated: latest?.created_at || group.updated_at,
      preview: latest?.text || "No messages yet",
      group_chats_sender: latest
        ? profiles.get(latest.sender_id) || creator
        : creator,
      grpconnect: creator,
      members: [...memberIdsForGroup].map((id) => profiles.get(id) || { id }),
      is_member: memberIdsForGroup.has(userId),
    };
  });
  return items.sort((a, b) => new Date(b.updated || 0) - new Date(a.updated || 0));
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
  await requireUserId();
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
  onPostChange,
  onBlogChange,
  onServiceNotificationChange,
  onAppNotificationChange,
}) {
  if (!supabase) return null;

  const channel = supabase
    .channel(`pulse:user:${userId}`, { config: { private: true } })
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

    .on("postgres_changes", { event: "*", schema: "public", table: "user_posts" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "user_post_likes" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "user_post_interactions" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "user_post_comments" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "user_post_comment_likes" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "user_post_comment_interactions" }, (payload) => onPostChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "blog_posts" }, (payload) => onBlogChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "blog_post_interactions" }, (payload) => onBlogChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "blog_post_shares" }, (payload) => onBlogChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notifications" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notification_likes" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notification_interactions" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notification_comments" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notification_comment_likes" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "service_notification_comment_interactions" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "polls" }, (payload) => onServiceNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "app_notifications" }, (payload) => onAppNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "app_notification_interactions" }, (payload) => onAppNotificationChange?.(payload))
    .on("postgres_changes", { event: "*", schema: "public", table: "app_notification_recipients" }, (payload) => onAppNotificationChange?.(payload))
    .subscribe((status, error) => {
      if (status === "CHANNEL_ERROR" || status === "TIMED_OUT" || status === "CLOSED") {
        console.error("[Pulse Realtime] Channel status:", status, error?.message || "");
      }
    });

  return channel;
}
