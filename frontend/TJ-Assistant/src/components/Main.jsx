import React, { useState, useRef, useEffect } from "react";
import robotIcon from "../assets/images/robot.png";
import sendButton from "../assets/images/send-btn.png";
import copyButton from "../assets/images/copy-btn.png";

const MarkdownRenderer = ({ text }) => {
    const parseMarkdown = (content) => {
        if (!content) return null;

        const lines = content.split('\n');
        let elements = [];
        let currentList = null;

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();

            if (!trimmedLine) {
                if (currentList) {
                    elements.push(currentList);
                    currentList = null;
                }
                return;
            }

            if (trimmedLine.startsWith('## ')) {
                const text = trimmedLine.substring(3);
                elements.push(
                    <h3 key={`h3-${index}`} className="markdown-heading">
                        {parseInlineMarkdown(text)}
                    </h3>
                );
            }

            else if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
                const text = trimmedLine.substring(2, trimmedLine.length - 2);
                elements.push(
                    <p key={`bold-${index}`} className="markdown-paragraph">
                        <strong>{text}</strong>
                    </p>
                );
            }

            else if (trimmedLine.match(/^[•\-\*]\s/)) {
                const text = trimmedLine.substring(2);
                if (!currentList) {
                    currentList = <ul key={`list-${index}`} className="markdown-list" />;
                }

                const listItem = (
                    <li key={`li-${index}`} className="markdown-list-item">
                        {parseInlineMarkdown(text)}
                    </li>
                );

                if (currentList.props.children) {
                    currentList = React.cloneElement(currentList, {
                        children: [...React.Children.toArray(currentList.props.children), listItem]
                    });
                } else {
                    currentList = React.cloneElement(currentList, {
                        children: listItem
                    });
                }
            }

            else if (trimmedLine.includes('[') && trimmedLine.includes(']')) {
                const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
                let match;
                let lastIndex = 0;
                let lineElements = [];

                while ((match = linkRegex.exec(trimmedLine)) !== null) {
                    if (match.index > lastIndex) {
                        lineElements.push(
                            <span key={`text-${match.index}`}>
                {parseInlineMarkdown(trimmedLine.substring(lastIndex, match.index))}
              </span>
                        );
                    }

                    lineElements.push(
                        <a
                            key={`link-${match.index}`}
                            href={match[2]}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="markdown-link"
                        >
                            {match[1]}
                        </a>
                    );

                    lastIndex = match.index + match[0].length;
                }

                if (lastIndex < trimmedLine.length) {
                    lineElements.push(
                        <span key={`text-end`}>
              {parseInlineMarkdown(trimmedLine.substring(lastIndex))}
            </span>
                    );
                }

                if (lineElements.length === 0) {
                    const simpleLinkRegex = /\[([^\]]+)\]/g;
                    lineElements = [];
                    lastIndex = 0;

                    while ((match = simpleLinkRegex.exec(trimmedLine)) !== null) {
                        if (match.index > lastIndex) {
                            lineElements.push(
                                <span key={`text-${match.index}`}>
                  {parseInlineMarkdown(trimmedLine.substring(lastIndex, match.index))}
                </span>
                            );
                        }

                        lineElements.push(
                            <span key={`bracket-${match.index}`} className="markdown-bracket">
                [{match[1]}]
              </span>
                        );

                        lastIndex = match.index + match[0].length;
                    }

                    if (lastIndex < trimmedLine.length) {
                        lineElements.push(
                            <span key={`text-end`}>
                {parseInlineMarkdown(trimmedLine.substring(lastIndex))}
              </span>
                        );
                    }
                }

                elements.push(
                    <p key={`link-line-${index}`} className="markdown-paragraph">
                        {lineElements}
                    </p>
                );
            }

            else {
                elements.push(
                    <p key={`para-${index}`} className="markdown-paragraph">
                        {parseInlineMarkdown(trimmedLine)}
                    </p>
                );
            }
        });

        if (currentList) {
            elements.push(currentList);
        }

        return elements;
    };

    const parseInlineMarkdown = (text) => {
        if (!text) return text;

        const elements = [];
        const boldRegex = /\*\*([^*]+)\*\*/g;
        let lastIndex = 0;
        let match;

        while ((match = boldRegex.exec(text)) !== null) {
            if (match.index > lastIndex) {
                elements.push(text.substring(lastIndex, match.index));
            }

            elements.push(<strong key={`bold-${match.index}`}>{match[1]}</strong>);

            lastIndex = match.index + match[0].length;
        }

        if (lastIndex < text.length) {
            elements.push(text.substring(lastIndex));
        }

        return elements.length > 0 ? elements : text;
    };

    return (
        <div className="markdown-content">
            {parseMarkdown(text)}
        </div>
    );
};

export default function Main({
                                 showChatHistory,
                                 currentChatId,
                                 messages,
                                 onSendMessage,
                                 isLoading
                             }) {
    const [message, setMessage] = useState("");
    const [copiedMessageId, setCopiedMessageId] = useState(null);
    const textareaRef = useRef(null);

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

    const handleSendMessage = async () => {
        if (message.trim() === "" || isLoading) return;
        const currentMessage = message;
        setMessage("");
        if (textareaRef.current) {
            textareaRef.current.style.height = '40px';
        }
        await onSendMessage(currentMessage);
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
                setTimeout(() => setCopiedMessageId(null), 2000);
            })
            .catch(err => console.error('Ошибка копирования:', err));
    };

    return (
        <main className="main">
            <section className="main-content" style={{
                left: showChatHistory ? '354px' : '4px',
                width: showChatHistory ? 'calc(100% - 350px)' : '100%'
            }}>
                {(currentChatId || messages.length === 0) && (
                    <div className="assistant-message welcome-message">
                        <div
                            className="welcome-info"
                        >
                            <img className="robot-icon" src={robotIcon} alt="robot icon" />
                            <h2 className="welcome-title">Ассистент Т-Ж</h2>
                        </div>

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
                )}

                <div className="messages-container">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`message-wrapper ${msg.type}-message-wrapper ${msg.isError ? 'error-message' : ''}`}
                        >
                            {msg.type === "user" ? (
                                <div className="user-message">
                                    <p className="user-message-text">{msg.text}</p>
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
                                    <div className="assistant-message-content">
                                        {msg.isError ? (
                                            <p className="assistant-message-text error-text">
                                                {msg.text}
                                            </p>
                                        ) : (
                                            <MarkdownRenderer text={msg.text} />
                                        )}
                                    </div>
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

            <section className="input-message-field" style={{
                left: showChatHistory ? 'calc(50% + 175px)' : '50%',
                transform: 'translateX(-50%)'
            }}>
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
            <div className="cover-messages"></div>
        </main>
    );
}