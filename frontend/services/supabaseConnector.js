import { supabase } from './supabase';

export const supabaseConnector = {
  connect: () => {
    // Supabase client is already initialized,
    // so there's no need for an explicit connect method.
    console.log('Supabase client initialized');
  },

  disconnect: () => {
    // Supabase client doesn't have a disconnect method.
    // We can remove all channels if needed.
    supabase.removeAllChannels();
    console.log('Supabase channels removed');
  },

  subscribe: (channelName, onMessage) => {
    const channel = supabase.channel(channelName);

    channel
      .on('postgres_changes', { event: '*', schema: 'public' }, (payload) => {
        onMessage(payload);
      })
      .subscribe((status, err) => {
        if (status === 'SUBSCRIBED') {
          console.log(`Subscribed to ${channelName}`);
        }
        if (status === 'CHANNEL_ERROR') {
          console.error(`Error subscribing to ${channelName}:`, err);
        }
        if (status === 'TIMED_OUT') {
          console.warn(`Timed out subscribing to ${channelName}`);
        }
        if (status === 'CLOSED') {
          console.log(`Unsubscribed from ${channelName}`);
        }
      });

    return channel;
  },

  unsubscribe: (channel) => {
    if (channel) {
      supabase.removeChannel(channel);
    }
  },
};
