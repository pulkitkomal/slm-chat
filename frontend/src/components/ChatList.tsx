import { useState } from "react";
import type { Agent, Chat } from "../api/client";
import { CreatePersona } from "./CreatePersona";

interface Props {
  agents: Agent[];
  chats: Chat[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onCreate: (agentId?: string) => void;
  onDelete: (id: string) => void;
  onAddAgent: (data: { name: string; avatar: string; title: string; system_message: string }) => void;
  onDeleteAgent: (id: string) => void;
  isMobile: boolean;
}

export function ChatList({ agents, chats, activeChatId, onSelect, onCreate, onDelete, onAddAgent, onDeleteAgent, isMobile }: Props) {
  const [showCreator, setShowCreator] = useState(false);

  return (
    <div style={{
      width: isMobile ? "100%" : 320,
      height: "100dvh",
      display: "flex",
      flexDirection: "column",
      background: "#000",
      borderRight: "1px solid #1c1c1e",
    }}>
      <div style={{
        padding: isMobile ? "calc(16px + var(--sat)) 16px 8px" : "16px 16px 8px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <h1 style={{ margin: 0, fontSize: isMobile ? 28 : 24, fontWeight: 700, color: "#fff", letterSpacing: -0.5 }}>
          Chats
        </h1>
        <button
          onClick={() => setShowCreator(true)}
          style={{
            width: isMobile ? 36 : 28, height: isMobile ? 36 : 28,
            borderRadius: "50%", border: "none", background: "#0a84ff",
            color: "#fff", fontSize: isMobile ? 20 : 16, cursor: "pointer", display: "flex",
            alignItems: "center", justifyContent: "center", fontWeight: 600,
          }}
        >
          +
        </button>
      </div>
      <div style={{ padding: "4px 0" }}>
        {agents.map((agent) => {
          const chat = chats.find((c) => c.agent_id === agent.id);
          const isActive = chat?.id === activeChatId;
          return (
            <div
              key={agent.id}
              onClick={() => { if (chat) onSelect(chat.id); else onCreate(agent.id); }}
              className="agent-row"
              style={{
                display: "flex", alignItems: "center", gap: 10, padding: "8px 16px",
                cursor: "pointer", background: isActive ? "#1c1c1e" : "transparent",
                transition: "background 0.15s",
              }}
            >
              <div style={{
                width: 40, height: 40, borderRadius: 20, display: "flex", alignItems: "center",
                justifyContent: "center", fontSize: 18, background: "#1c1c1e", flexShrink: 0,
              }}>
                {agent.avatar}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: "#fff", fontWeight: 600, fontSize: 14 }}>{agent.name}</div>
                <div style={{ color: "#8e8e93", fontSize: 11 }}>{agent.title}</div>
              </div>
              {chat && <div style={{ width: 8, height: 8, borderRadius: 4, background: "#30d158", flexShrink: 0 }} />}
              <button
                onClick={(e) => { e.stopPropagation(); onDeleteAgent(agent.id); }}
                className="delete-btn"
                style={{
                  background: "none", border: "none", color: "#555", cursor: "pointer",
                  fontSize: 11, padding: 2, opacity: 0, transition: "opacity 0.15s",
                }}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
      <div style={{
        padding: "6px 16px 4px", color: "#8e8e93", fontSize: 12,
        textTransform: "uppercase", letterSpacing: 0.5, fontWeight: 600,
      }}>
        History ({chats.length})
      </div>
      <div style={{ flex: 1, overflowY: "auto", paddingBottom: 8 }}>
        {chats.length === 0 ? (
          <div style={{ padding: "8px 16px", color: "#555", fontSize: 13, textAlign: "center" }}>
            No conversations yet
          </div>
        ) : (
          chats.map((chat) => {
            const agent = agents.find((a) => a.id === chat.agent_id);
            return (
              <div
                key={chat.id}
                onClick={() => onSelect(chat.id)}
                className="history-row"
                style={{
                  padding: "6px 16px", cursor: "pointer",
                  background: chat.id === activeChatId ? "#1c1c1e" : "transparent",
                  display: "flex", alignItems: "center", gap: 8,
                }}
              >
                {agent && <span style={{ fontSize: 14, flexShrink: 0 }}>{agent.avatar}</span>}
                <span style={{ color: "#ebebf5", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, fontSize: 13 }}>
                  {chat.title}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(chat.id); }}
                  className="delete-btn"
                  style={{
                    background: "none", border: "none", color: "#555", cursor: "pointer",
                    fontSize: 11, padding: 2, opacity: 0, transition: "opacity 0.15s", flexShrink: 0,
                  }}
                >
                  ✕
                </button>
              </div>
            );
          })
        )}
      </div>
      {showCreator && (
        <CreatePersona
          onSave={(data) => { onAddAgent(data); setShowCreator(false); }}
          onClose={() => setShowCreator(false)}
        />
      )}
    </div>
  );
}
