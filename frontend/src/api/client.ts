const API_BASE = import.meta.env.VITE_API_URL || "";

export interface Agent {
  id: string;
  name: string;
  avatar: string;
  title: string;
  system_message: string;
}

export interface Chat {
  id: string;
  agent_id: string | null;
  title: string;
  system_message: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface GraphData {
  nodes: { id: string; label: string; node_type: string; properties: Record<string, unknown> }[];
  edges: { source: string; target: string; relation: string; weight: number }[];
}

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  listAgents: () => request<{ agents: Agent[] }>("/api/agents"),
  createAgent: (data: { name: string; avatar?: string; title?: string; system_message?: string }) =>
    request<Agent>("/api/agents", { method: "POST", body: JSON.stringify(data) }),
  deleteAgent: (id: string) =>
    request<{ message: string }>(`/api/agents/${id}`, { method: "DELETE" }),
  listChats: () => request<{ chats: Chat[] }>("/api/chats"),
  createChat: (title: string, system_message = "", agent_id?: string) =>
    request<Chat>("/api/chats", { method: "POST", body: JSON.stringify({ title, system_message, agent_id }) }),
  getChat: (id: string) => request<Chat>(`/api/chats/${id}`),
  updateChat: (id: string, data: Partial<Chat>) =>
    request<Chat>(`/api/chats/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  resetChat: (id: string) =>
    request<{ message: string }>(`/api/chats/${id}/reset`, { method: "POST" }),
  deleteChat: (id: string) =>
    request<{ message: string }>(`/api/chats/${id}`, { method: "DELETE" }),
  listMessages: (chatId: string) =>
    request<{ messages: Message[] }>(`/api/chats/${chatId}/messages`),
  sendMessage: (chatId: string, content: string) =>
    request<Message>(`/api/chats/${chatId}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  streamUrl: (chatId: string) => `${API_BASE}/api/chats/${chatId}/stream`,
  getGraph: (chatId: string) => request<GraphData>(`/api/chats/${chatId}/graph`),
  getEmotion: (chatId: string) => request<{ emotion: string; intensity: number; timestamp?: string }>(`/api/chats/${chatId}/emotion`),
};
