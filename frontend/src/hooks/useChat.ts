import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import type { Chat, Message } from "../api/client";

export function useChat() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [loading, setLoading] = useState(false);
  const activeChat = chats.find((c) => c.id === activeChatId) || null;

  const loadChats = useCallback(async () => {
    const data = await api.listChats();
    setChats(data.chats);
  }, []);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  const selectChat = useCallback(async (id: string) => {
    setActiveChatId(id);
    setStreamingContent("");
    const data = await api.listMessages(id);
    setMessages(data.messages);
  }, []);

  const createChat = useCallback(async (title?: string) => {
    const chat = await api.createChat(title || "New Chat");
    setChats((prev) => [chat, ...prev]);
    return chat;
  }, []);

  const updateChat = useCallback(async (id: string, data: Partial<Chat>) => {
    const updated = await api.updateChat(id, data);
    setChats((prev) => prev.map((c) => (c.id === id ? updated : c)));
  }, []);

  const deleteChat = useCallback(async (id: string) => {
    await api.deleteChat(id);
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
      setMessages([]);
    }
  }, [activeChatId]);

  const resetChat = useCallback(async (id: string) => {
    await api.resetChat(id);
    setMessages([]);
    setStreamingContent("");
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!activeChatId) return;
    setLoading(true);
    setStreamingContent("");

    const userMsg: Message = {
      id: "temp",
      chat_id: activeChatId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const streamUrl = api.streamUrl(activeChatId);
    const res = await fetch(streamUrl, {
      method: "GET",
      headers: { Accept: "text/event-stream" },
    });

    if (!res.ok) {
      setLoading(false);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      setLoading(false);
      return;
    }

    const decoder = new TextDecoder();
    let full = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            setMessages((prev) => [
              ...prev,
              {
                id: "streamed",
                chat_id: activeChatId,
                role: "assistant",
                content: full,
                created_at: new Date().toISOString(),
              },
            ]);
            setStreamingContent("");
          } else {
            full += data;
            setStreamingContent(full);
          }
        }
      }
    }
    setLoading(false);
  }, [activeChatId]);

  return {
    chats,
    activeChatId,
    activeChat,
    messages,
    streamingContent,
    loading,
    selectChat,
    createChat,
    updateChat,
    deleteChat,
    resetChat,
    sendMessage,
  };
}
