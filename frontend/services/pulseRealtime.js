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

function mapDirectMessage(row, profiles, currentUserId) {
  return {
    ...row,
    created: row.created_at,
    image: row.image_path || null,
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
  const messages = (rows || []).slice(0, pageSize).map((row) =>
    mapDirectMessage(row, profiles, userId)
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

  return connections.map((connection) => {
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
      image: latest?.image_path || null,
      updated: latest?.created_at || connection.updated_at,
    };
  });
}

export async function sendDirectMessage(details) {
  const userId = await requireUserId();
  if (details?.image) {
    throw new Error("Image messages need the secured Supabase Storage upload path, which is being configured separately. Text messages are available now.");
  }
  const message = String(details?.message || "");
  if (!message.trim() || message.length > 10000) {
    throw new Error("Enter a message of up to 10,000 characters.");
  }

  const { data, error } = await supabase
    .from("direct_messages")
    .insert({
      connection_id: details.connectionId,
      sender_id: userId,
      description: message,
    })
    .select("id,connection_id,sender_id,image_path,red,description,created_at")
    .single();

  if (error) throw error;
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
