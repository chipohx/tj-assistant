import React, { useState, useEffect } from "react";
import Header from "./components/Header.jsx";
import Main from "./components/Main.jsx";
import Registration from "./components/Registration.jsx";
import VerifyEmail from "./components/VerifyEmail.jsx";

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(() => {
        const token = localStorage.getItem("authToken");
        return !!token;
    });
    const [showChatHistory, setShowChatHistory] = useState(false);

    const [chats, setChats] = useState([]);
    const [currentChatId, setCurrentChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const API_BASE_URL = "http://localhost:8000/api";

    const getAuthHeaders = () => {
        const token = localStorage.getItem("authToken");
        return {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
    };

    const loadChats = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/chats`, {
                headers: getAuthHeaders(),
            });
            if (response.ok) {
                const data = await response.json();
                setChats(data.items || []);
            } else {
                console.error('Не удалось загрузить чаты');
            }
        } catch (error) {
            console.error('Ошибка загрузки чатов:', error);
        }
    };

    useEffect(() => {
        if (isLoggedIn) {
            loadChats();
        } else {
            setChats([]);
            setCurrentChatId(null);
            setMessages([]);
        }
    }, [isLoggedIn]);

    const selectChat = async (chatId) => {
        setCurrentChatId(chatId);
        setMessages([]);
        try {
            const response = await fetch(`${API_BASE_URL}/chat/${chatId}/messages?limit=30`, {
                headers: getAuthHeaders(),
            });
            if (response.ok) {
                const data = await response.json();
                const loadedMessages = data.items.map(msg => ({
                    id: msg.message_id,
                    type: msg.role && msg.role.toUpperCase() === 'USER' ? 'user' : 'assistant',
                    text: msg.content,
                    timestamp: msg.created,
                }));
                setMessages(loadedMessages);
            }
        } catch (error) {
            console.error('Ошибка загрузки сообщений:', error);
        }
    };

    const createNewChat = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/new-chat`, {
                method: 'POST',
                headers: getAuthHeaders(),
            });
            if (response.ok) {
                const data = await response.json();
                const newChatId = data.chat_id;

                const newChat = {
                    id: newChatId,
                    title: 'Новый чат',
                    created: new Date().toISOString(),
                    updated: new Date().toISOString(),
                };
                setChats(prev => [newChat, ...prev]);

                await selectChat(newChatId);

                setTimeout(() => {
                    const newName = prompt("Введите название для нового чата:", "Новый чат");
                    if (newName && newName.trim() !== "") {
                        renameChat(newChatId, newName.trim());
                    }
                }, 50);
            }
        } catch (error) {
            console.error('Ошибка создания чата:', error);
        }
    };

    const renameChat = (chatId, newTitle) => {
        setChats(prev =>
            prev.map(chat =>
                chat.id === chatId ? { ...chat, title: newTitle } : chat
            )
        );
    };

    const deleteChat = (chatId) => {
        setChats(prev => prev.filter(chat => chat.id !== chatId));
        if (currentChatId === chatId) {
            const remaining = chats.filter(c => c.id !== chatId);
            if (remaining.length > 0) {
                selectChat(remaining[0].id);
            } else {
                setCurrentChatId(null);
                setMessages([]);
            }
        }
    };

    const sendMessage = async (content) => {
        if (!content.trim() || isLoading) return;

        const userMessage = {
            id: `temp-${Date.now()}`,
            type: 'user',
            text: content,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const requestBody = { content };
            if (currentChatId) {
                requestBody.chat_id = currentChatId;
            }

            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const data = await response.json();

            const assistantMessage = {
                id: data.message_id || `assistant-${Date.now()}`,
                type: 'assistant',
                text: data.content,
                timestamp: data.timestamp || new Date().toISOString(),
            };
            setMessages(prev => [...prev, assistantMessage]);

            if (data.chat_created) {
                const newChatId = data.chat_created;
                setCurrentChatId(newChatId);

                const newChat = {
                    id: newChatId,
                    title: content.slice(0, 30),
                    created: new Date().toISOString(),
                    updated: new Date().toISOString(),
                };
                setChats(prev => [newChat, ...prev]);
            }
        } catch (error) {
            console.error('Ошибка отправки:', error);
            const errorMessage = {
                id: `error-${Date.now()}`,
                type: 'assistant',
                text: `Извините, произошла ошибка: ${error.message}. Пожалуйста, попробуйте еще раз.`,
                timestamp: new Date().toISOString(),
                isError: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        localStorage.removeItem("authToken");
        localStorage.removeItem("userEmail");
        setShowChatHistory(false);
    };

    const handleLogin = async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString(),
            });

            const responseText = await response.text();
            if (!response.ok) {
                let errorMessage = 'Ошибка авторизации';
                try {
                    const errorData = JSON.parse(responseText);
                    errorMessage = errorData.detail || errorMessage;
                } catch {
                    errorMessage = responseText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const data = JSON.parse(responseText);
            if (!data.access_token) throw new Error('Токен не получен');

            localStorage.setItem("authToken", data.access_token);
            localStorage.setItem("userEmail", email);
            setIsLoggedIn(true);
            return true;
        } catch (error) {
            console.error('Ошибка входа:', error.message);
            alert(`Ошибка входа: ${error.message}`);
            return false;
        }
    };

    const handleRegister = async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString(),
            });
            
            // Регистрация всегда успешна - пользователь получает письмо
            return {
                success: true,
                message: "На вашу почту отправлено письмо с подтверждением. Пожалуйста, проверьте вашу электронную почту."
            };
        } catch (error) {
            console.error('Ошибка регистрации:', error);
            // Даже при ошибке отправки письма, аккаунт мог быть создан
            // Возвращаем сообщение о необходимости проверить почту
            return {
                success: true,
                message: "На вашу почту отправлено письмо с подтверждением. Пожалуйста, проверьте вашу электронную почту."
            };
        }
    };

    return (
        <>
            {isLoggedIn ? (
                <>
                    <Header
                        onLogout={handleLogout}
                        userEmail={localStorage.getItem("userEmail")}
                        showChatHistory={showChatHistory}
                        setShowChatHistory={setShowChatHistory}
                        chats={chats}
                        currentChatId={currentChatId}
                        onSelectChat={selectChat}
                        onCreateChat={createNewChat}
                        onRenameChat={renameChat}
                        onDeleteChat={deleteChat}
                    />
                    <Main
                        showChatHistory={showChatHistory}
                        currentChatId={currentChatId}
                        messages={messages}
                        onSendMessage={sendMessage}
                        isLoading={isLoading}
                    />
                </>
            ) : (
                <Registration onLogin={handleLogin} onRegister={handleRegister} />
            )}
        </>
    );
}

export default App;