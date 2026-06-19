import { ChatList } from "./components/ChatList";
import { ChatWindow } from "./components/ChatWindow";
import { useChat } from "./hooks/useChat";

export default function App() {
  const {
    chats, activeChatId, activeChat, messages, streamingContent, loading, error,
    selectChat, createChat, updateChat, deleteChat, resetChat, sendMessage,
  } = useChat();

  return (
    <div style={{ display: "flex", height: "100vh", background: "#121212", color: "#eee", fontFamily: "system-ui, sans-serif" }}>
      <ChatList
        chats={chats}
        activeChatId={activeChatId}
        onSelect={selectChat}
        onCreate={() => createChat()}
        onDelete={deleteChat}
      />
      {activeChat ? (
        <ChatWindow
          chat={activeChat}
          messages={messages}
          streamingContent={streamingContent}
          loading={loading}
          error={error}
          onSend={sendMessage}
          onUpdateChat={updateChat}
          onReset={resetChat}
        />
      ) : (
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#666" }}>
          Select or create a chat to begin
        </div>
      )}
    </div>
  );
}
