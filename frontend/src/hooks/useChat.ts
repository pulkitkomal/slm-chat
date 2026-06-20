import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import type { Chat, Message } from "../api/client";
import type { Agent } from "../api/client";

export function useChat() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentEmotion, setCurrentEmotion] = useState<{ emotion: string; intensity: number } | null>(null);
  const activeChat = chats.find((c) => c.id === activeChatId) || null;
  const activeAgent = agents.find((a) => a.id === activeChat?.agent_id) || null;

  const loadAgents = useCallback(async () => {
    try {
      setError(null);
      const data = await api.listAgents();
      setAgents(data.agents);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, []);

  const loadChats = useCallback(async () => {
    try {
      setError(null);
      const data = await api.listChats();
      setChats(data.chats);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, []);

  useEffect(() => {
    loadAgents();
    loadChats();
  }, [loadAgents, loadChats]);

  const loadEmotion = useCallback(async (id: string) => {
    try {
      const data = await api.getEmotion(id);
      setCurrentEmotion(data);
    } catch {
      setCurrentEmotion(null);
    }
  }, []);

  const selectChat = useCallback(async (id: string) => {
    try {
      setError(null);
      setActiveChatId(id);
      setStreamingContent("");
      const data = await api.listMessages(id);
      setMessages(data.messages);
      loadEmotion(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, [loadEmotion]);

  const createAgent = useCallback(async (data: { name: string; avatar?: string; title?: string; system_message?: string }) => {
    try {
      setError(null);
      const agent = await api.createAgent(data);
      setAgents((prev) => [...prev, agent]);
      return agent;
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
      throw e;
    }
  }, []);

  const deleteAgent = useCallback(async (id: string) => {
    try {
      setError(null);
      await api.deleteAgent(id);
      setAgents((prev) => prev.filter((a) => a.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, []);

  const createChat = useCallback(async (title?: string, agent_id?: string) => {
    try {
      setError(null);
      const chat = await api.createChat(title || "New Chat", "", agent_id);
      setChats((prev) => [chat, ...prev]);
      return chat;
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
      throw e;
    }
  }, []);

  const updateChat = useCallback(async (id: string, data: Partial<Chat>) => {
    try {
      setError(null);
      const updated = await api.updateChat(id, data);
      setChats((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, []);

  const deleteChat = useCallback(async (id: string) => {
    try {
      setError(null);
      await api.deleteChat(id);
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (activeChatId === id) {
        setActiveChatId(null);
        setMessages([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, [activeChatId]);

  const resetChat = useCallback(async (id: string) => {
    try {
      setError(null);
      await api.resetChat(id);
      setMessages([]);
      setStreamingContent("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!activeChatId) return;
    setError(null);
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

    try {
      const streamUrl = `${api.streamUrl(activeChatId)}?q=${encodeURIComponent(content)}`;
      const res = await fetch(streamUrl, {
        method: "GET",
        headers: { Accept: "text/event-stream" },
      });

      if (!res.ok) {
        setError(`HTTP ${res.status}: ${await res.text()}`);
        setLoading(false);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        setError("Stream not available");
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
      if (activeChatId) loadEmotion(activeChatId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    }
    setLoading(false);
  }, [activeChatId, loadEmotion]);

  return {
    agents,
    chats,
    activeChatId,
    activeChat,
    activeAgent,
    messages,
    streamingContent,
    loading,
    error,
    currentEmotion,
    selectChat,
    createChat,
    updateChat,
    deleteChat,
    createAgent,
    deleteAgent,
    resetChat,
    sendMessage,
  };
}
