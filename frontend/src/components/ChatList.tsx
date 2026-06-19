import type { Chat } from "../api/client";

interface Props {
  chats: Chat[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

export function ChatList({ chats, activeChatId, onSelect, onCreate, onDelete }: Props) {
  return (
    <div style={{ width: 260, borderRight: "1px solid #333", height: "100vh", display: "flex", flexDirection: "column", background: "#1a1a1a" }}>
      <div style={{ padding: "12px", borderBottom: "1px solid #333" }}>
        <button
          onClick={onCreate}
          style={{ width: "100%", padding: "8px", background: "#2d2d2d", color: "#fff", border: "1px solid #555", borderRadius: 6, cursor: "pointer" }}
        >
          + New Chat
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => onSelect(chat.id)}
            style={{
              padding: "10px 12px",
              cursor: "pointer",
              background: chat.id === activeChatId ? "#2d2d2d" : "transparent",
              borderBottom: "1px solid #2a2a2a",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ color: "#ddd", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
              {chat.title}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(chat.id); }}
              style={{ background: "none", border: "none", color: "#666", cursor: "pointer", fontSize: 12 }}
            >
              x
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
