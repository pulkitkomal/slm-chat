import { useState, useEffect } from "react";
import { ChatList } from "./components/ChatList";
import { ChatWindow } from "./components/ChatWindow";
import { useChat } from "./hooks/useChat";
import { useIsMobile } from "./hooks/useMediaQuery";

export default function App() {
  const {
    agents, chats, activeChatId, activeChat, activeAgent, messages, streamingContent, loading, error,
    currentEmotion,
    selectChat, createChat, updateChat, deleteChat, createAgent, deleteAgent, resetChat, sendMessage,
  } = useChat();

  const isMobile = useIsMobile();
  const [ready, setReady] = useState(false);
  const [showList, setShowList] = useState(true);

  useEffect(() => {
    setShowList(isMobile);
    setReady(true);
  }, [isMobile]);

  if (!ready) return null;

  const handleSelect = async (id: string) => {
    await selectChat(id);
    if (isMobile) setShowList(false);
  };

  const handleCreate = async (agentId?: string) => {
    const chat = await createChat(undefined, agentId);
    if (chat) {
      await selectChat(chat.id);
      if (isMobile) setShowList(false);
    }
  };

  const handleBack = () => setShowList(true);

  const showChat = activeChat && (!isMobile || !showList);

  return (
    <div style={{
      display: "flex", height: "100dvh", background: "#000", color: "#fff",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif",
    }}>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        html, body, #root { height: 100dvh; overflow: hidden; overscroll-behavior: none; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #3a3a3c; border-radius: 2px; }
        .agent-row:hover .delete-btn,
        .history-row:hover .delete-btn { opacity: 0.5 !important; }
        .agent-row:hover { background: #111 !important; }
        .history-row:hover { background: #111 !important; }
        .agent-row { min-height: 48px; }
        .history-row { min-height: 40px; }
      `}</style>
      {(!isMobile || showList) && (
        <ChatList
          agents={agents}
          chats={chats}
          activeChatId={activeChatId}
          onSelect={handleSelect}
          onCreate={handleCreate}
          onDelete={deleteChat}
          onAddAgent={createAgent}
          onDeleteAgent={deleteAgent}
          isMobile={isMobile}
        />
      )}
      {showChat ? (
        <ChatWindow
          chat={activeChat}
          agent={activeAgent}
          messages={messages}
          streamingContent={streamingContent}
          loading={loading}
          error={error}
          isMobile={isMobile}
          currentEmotion={currentEmotion}
          onBack={handleBack}
          onSend={sendMessage}
          onUpdateChat={updateChat}
          onReset={resetChat}
        />
      ) : isMobile && showList ? null : (
        <div style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 12,
        }}>
          <div style={{ fontSize: 48, opacity: 0.15 }}>💬</div>
          <div style={{ fontSize: 14, color: "#555" }}>Pick a character to start chatting</div>
        </div>
      )}
    </div>
  );
}
