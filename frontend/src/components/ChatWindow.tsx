import type { Chat, Message } from "../api/client";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { SystemMessageEditor } from "./SystemMessageEditor";

interface Props {
  chat: Chat;
  messages: Message[];
  streamingContent: string;
  loading: boolean;
  error: string | null;
  onSend: (content: string) => void;
  onUpdateChat: (id: string, data: Partial<Chat>) => void;
  onReset: (id: string) => void;
}

export function ChatWindow({ chat, messages, streamingContent, loading, error, onSend, onUpdateChat, onReset }: Props) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #333", display: "flex", justifyContent: "space-between", alignItems: "center", background: "#1a1a1a" }}>
        <h2 style={{ margin: 0, color: "#eee", fontSize: 16 }}>{chat.title}</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <SystemMessageEditor
            systemMessage={chat.system_message}
            onSave={(msg) => onUpdateChat(chat.id, { system_message: msg })}
          />
          <button
            onClick={() => onReset(chat.id)}
            style={{ background: "none", border: "1px solid #555", color: "#aaa", borderRadius: 4, padding: "4px 8px", cursor: "pointer", fontSize: 12 }}
          >
            Reset
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 16, background: "#121212" }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {streamingContent && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
            <div style={{ maxWidth: "70%", padding: "10px 14px", borderRadius: 12, background: "#2d2d2d", color: "#eee", whiteSpace: "pre-wrap" }}>
              {streamingContent}
            </div>
          </div>
        )}
      </div>
      {error && (
        <div style={{ padding: "8px 16px", background: "#5c1a1a", color: "#ff8a8a", fontSize: 13, textAlign: "center", borderTop: "1px solid #7a2a2a" }}>
          {error}
        </div>
      )}
      <MessageInput onSend={onSend} disabled={loading} />
    </div>
  );
}
