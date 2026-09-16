import { useEffect, useMemo, useRef, useState } from "react";
import Layout from "./Layout";
import { Loading } from "./ui";
import api from "../api/axiosClient";
import { useAuth } from "../context/AuthContext";

export default function ChatApp({ title }) {
  const { user } = useAuth();
  const [contacts, setContacts] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConvo, setActiveConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    Promise.all([api.get("/chat/contacts/"), api.get("/chat/conversations/")])
      .then(([c, conv]) => {
        setContacts(c.data);
        setConversations(conv.data.results ?? conv.data);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeConvo) return;
    api.get(`/chat/conversations/${activeConvo.id}/messages/`).then((res) => {
      setMessages(res.data.results ?? res.data);
    });

    const token = localStorage.getItem("access");
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${activeConvo.id}/?token=${token}`);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [activeConvo?.id]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function openContact(contact) {
    const res = await api.post("/chat/start/", { user_id: contact.id });
    setActiveConvo(res.data);
    setConversations((prev) => {
      const exists = prev.find((c) => c.id === res.data.id);
      return exists ? prev : [res.data, ...prev];
    });
  }

  function send() {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text: trimmed }));
    } else {
      api.post(`/chat/conversations/${activeConvo.id}/messages/`, { text: trimmed }).then((res) => {
        setMessages((prev) => [...prev, res.data]);
      });
    }
    setText("");
  }

  const otherPartyName = (convo) =>
    convo.participants?.find((p) => p.email !== user?.email)?.first_name || "Conversation";

  const conversationOptions = useMemo(() => {
    // Merge contacts with any existing conversation partner not in contacts anymore.
    return conversations;
  }, [conversations]);

  return (
    <Layout title={title}>
      {loading ? (
        <Loading />
      ) : (
        <div className="two-col">
          <div>
            <div className="card" style={{ marginBottom: 12 }}>
              <h4 style={{ marginTop: 0 }}>Start a conversation</h4>
              {contacts.length === 0 && (
                <p style={{ color: "#64748b", fontSize: "0.85rem" }}>No contacts available yet.</p>
              )}
              {contacts.map((c) => (
                <button key={c.id} className="list-item-btn" onClick={() => openContact(c)}>
                  {c.first_name} {c.last_name} <span style={{ color: "#64748b" }}>({c.role})</span>
                </button>
              ))}
            </div>
            <div className="card">
              <h4 style={{ marginTop: 0 }}>Conversations</h4>
              {conversationOptions.length === 0 && (
                <p style={{ color: "#64748b", fontSize: "0.85rem" }}>No conversations yet.</p>
              )}
              {conversationOptions.map((c) => (
                <button
                  key={c.id}
                  className={`list-item-btn ${activeConvo?.id === c.id ? "active" : ""}`}
                  onClick={() => setActiveConvo(c)}
                >
                  {otherPartyName(c)}
                </button>
              ))}
            </div>
          </div>

          <div className="chat-window">
            {!activeConvo ? (
              <div className="empty-state" style={{ margin: "auto" }}>
                Select or start a conversation to begin messaging.
              </div>
            ) : (
              <>
                <div className="chat-messages" ref={scrollRef}>
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={`chat-bubble ${m.sender.email === user?.email ? "mine" : "theirs"}`}
                    >
                      {m.text}
                    </div>
                  ))}
                </div>
                <div className="chat-input">
                  <input
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && send()}
                    placeholder="Type a message…"
                  />
                  <button className="btn btn-primary" onClick={send}>
                    Send
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
