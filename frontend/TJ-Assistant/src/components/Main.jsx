import React, { useState, useRef, useEffect } from "react";
import robotIcon from "../assets/images/robot.png";
import sendButton from "../assets/images/send-btn.png";
import copyButton from "../assets/images/copy-btn.png";

export default function Main() {
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState([]);
    const [copiedMessageId, setCopiedMessageId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentChatId, setCurrentChatId] = useState(null);
    const textareaRef = useRef(null);

    const API_BASE_URL = "http://localhost:8000/api";

    const adjustTextareaHeight = () => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            const maxHeight = 120;
            const newHeight = Math.min(textarea.scrollHeight, maxHeight);
            textarea.style.height = newHeight + 'px';
        }
    };

    useEffect(() => {
        adjustTextareaHeight();
    }, [message]);

    const sendMessageToServer = async (content, chatId = null) => {
        try {
            const token = localStorage.getItem("authToken");
            const headers = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const requestBody = {
                content: content,
            };

            if (chatId) {
                requestBody.chat_id = chatId;
            }

            console.log("Отправка запроса на /chat:", {
                url: `${API_BASE_URL}/chat`,
                headers,
                body: requestBody
            });

            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: "POST",
                headers: headers,
                body: JSON.stringify(requestBody),
                credentials: "include"
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error("Ошибка сервера:", response.status, errorText);

                let errorMessage = `Ошибка: ${response.status}`;
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.detail) {
                        errorMessage = errorJson.detail;
                    }
                } catch (e) {
                    if (errorText) {
                        errorMessage = errorText;
                    }
                }

                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log("Ответ от сервера:", data);
            return data;
        } catch (error) {
            console.error("Ошибка при отправке сообщения:", error);
            throw error;
        }
    };

    const handleSendMessage = async () => {
        if (message.trim() === "" || isLoading) return;

        const userMessage = {
            id: Date.now().toString(),
            type: "user",
            text: message,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        const currentMessage = message;
        setMessage("");
        setIsLoading(true);

        if (textareaRef.current) {
            textareaRef.current.style.height = '40px';
        }

        try {
            const response = await sendMessageToServer(currentMessage, currentChatId);

            const assistantMessage = {
                id: response.message_id || `assistant-${Date.now()}`,
                type: "assistant",
                text: response.content,
                timestamp: response.timestamp || new Date().toISOString()
            };

            setMessages(prev => [...prev, assistantMessage]);

            if (response.chat_created && !currentChatId) {
                setCurrentChatId(response.chat_created);
                console.log("Создан новый чат с ID:", response.chat_created);
            }
        } catch (error) {
            console.error("Полная ошибка:", error);
            const errorMessage = {
                id: `error-${Date.now()}`,
                type: "assistant",
                text: `Извините, произошла ошибка: ${error.message}. Пожалуйста, попробуйте еще раз.`,
                timestamp: new Date().toISOString(),
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleAssistantButtonClick = (buttonText) => {
        setMessage(buttonText);
        setTimeout(() => {
            handleSendMessage();
        }, 100);
    };

    const handleCopyText = (text, messageId) => {
        navigator.clipboard.writeText(text)
            .then(() => {
                setCopiedMessageId(messageId);
                setTimeout(() => {
                    setCopiedMessageId(null);
                }, 2000);
            })
            .catch(err => {
                console.error('Ошибка при копировании текста: ', err);
            });
    };

    return (
        <main className="main">
            <section className="main-content">
                <div className="assistant-message welcome-message">
                    <img className="robot-icon" src={robotIcon} alt="robot icon" />
                    <p className="assistant-message-text">
                        Привет! Я Ассистент Т-Ж — AI-эксперт по статьям.
                    </p>
                    <p className="assistant-message-text1">
                        Спросите о финансах, инвестициях, правах, путешествиях или любой другой теме, и я найду для вас ответ в статьях Т-Ж.
                    </p>
                    <p className="assistant-message-text2">Попробуйте задать вопрос:</p>
                    <div className="assistant-message-buttons">
                        <button
                            className="assistant-message-button"
                            onClick={() => handleAssistantButtonClick("Как взять ипотеку?")}
                        >
                            Как взять ипотеку?
                        </button>
                        <button
                            className="assistant-message-button"
                            onClick={() => handleAssistantButtonClick("Налоги для самозанятых")}
                        >
                            Налоги для самозанятых
                        </button>
                        <button
                            className="assistant-message-button"
                            onClick={() => handleAssistantButtonClick("Как экономить на путешествиях?")}
                        >
                            Как экономить на путешествиях?
                        </button>
                        <button
                            className="assistant-message-button"
                            onClick={() => handleAssistantButtonClick("Страхование автомобиля")}
                        >
                            Страхование автомобиля
                        </button>
                    </div>
                </div>
                <div className="messages-container">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`message-wrapper ${msg.type}-message-wrapper ${msg.isError ? 'error-message' : ''}`}
                        >
                            {msg.type === "user" ? (
                                <div className="user-message">
                                    <p className="user-message-text">
                                        {msg.text}
                                    </p>
                                    <img
                                        className="copy-icon"
                                        src={copyButton}
                                        alt="copy button"
                                        onClick={() => handleCopyText(msg.text, msg.id)}
                                    />
                                    {copiedMessageId === msg.id && (
                                        <div className="copy-tooltip">Скопировано</div>
                                    )}
                                </div>
                            ) : (
                                <div className="assistant-message dynamic-message">
                                    <p className="assistant-message-text">
                                        {msg.text}
                                    </p>
                                    <img
                                        className="copy-assistant-icon"
                                        src={copyButton}
                                        alt="copy button"
                                        onClick={() => handleCopyText(msg.text, msg.id)}
                                    />
                                    {copiedMessageId === msg.id && (
                                        <div className="copy-tooltip">Скопировано</div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="message-wrapper assistant-message-wrapper">
                            <div className="assistant-message dynamic-message">
                                <div className="loading-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            <section className="input-message-field">
                <textarea
                    ref={textareaRef}
                    className="message-field"
                    placeholder="Задайте вопрос о финансах, законах, путешествиях..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    rows={1}
                    disabled={isLoading}
                />
                <button
                    className="send-message-button"
                    onClick={handleSendMessage}
                    disabled={isLoading}
                    style={{
                        backgroundImage: `url(${sendButton})`,
                        backgroundSize: "contain",
                        backgroundRepeat: "no-repeat",
                        opacity: isLoading ? 0.5 : 1
                    }}
                ></button>
            </section>
        </main>
    );
}