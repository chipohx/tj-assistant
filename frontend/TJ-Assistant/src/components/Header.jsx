import React, { useState } from "react";
import logo from "../assets/images/robot.png";
import questionIcon from "../assets/images/question.png";
import updated from "../assets/images/chats.png";
import plus from "../assets/images/plus.png";
import profilelogo from "../assets/images/account.png";

export default function Header({
                                   onLogout,
                                   userEmail,
                                   showChatHistory,
                                   setShowChatHistory,
                                   chats,
                                   currentChatId,
                                   onSelectChat,
                                   onCreateChat,
                                   onRenameChat,
                                   onDeleteChat
                               }) {
    const [activeChatMenu, setActiveChatMenu] = useState(null);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    const getNicknameFromEmail = () => {
        if (!userEmail) return "Пользователь";
        const atIndex = userEmail.indexOf('@');
        if (atIndex === -1) return userEmail;
        return userEmail.substring(0, atIndex);
    };
    const nickname = getNicknameFromEmail();

    const toggleHelp = () => setShowHelp(!showHelp);
    const closeHelp = () => setShowHelp(false);

    const toggleChatHistory = () => {
        setShowChatHistory(!showChatHistory);
        setActiveChatMenu(null);
        setShowProfileMenu(false);
    };

    const closeChatHistory = () => {
        setShowChatHistory(false);
        setActiveChatMenu(null);
        setShowProfileMenu(false);
    };

    const handleLogoutClick = () => {
        if (onLogout) onLogout();
    };

    const handleChatPointsClick = (chatId, e) => {
        e.stopPropagation();
        setActiveChatMenu(activeChatMenu === chatId ? null : chatId);
        setShowProfileMenu(false);
    };

    const handleProfilePointsClick = (e) => {
        e.stopPropagation();
        setShowProfileMenu(!showProfileMenu);
        setActiveChatMenu(null);
    };

    const handleCreateNewChat = () => {
        onCreateChat(); // теперь создаёт через API
    };

    const handleRenameChat = (chatId) => {
        const currentTitle = chats.find(chat => chat.id === chatId)?.title || "";
        const newName = prompt("Введите новое название чата:", currentTitle);
        if (newName && newName.trim() !== "") {
            onRenameChat(chatId, newName.trim());
        }
        setActiveChatMenu(null);
    };

    const handleDeleteChat = (chatId) => {
        if (window.confirm("Вы уверены, что хотите удалить этот чат?")) {
            onDeleteChat(chatId);
        }
        setActiveChatMenu(null);
    };

    React.useEffect(() => {
        const handleClickOutside = () => {
            setActiveChatMenu(null);
            setShowProfileMenu(false);
        };
        if (showChatHistory) {
            document.addEventListener('click', handleClickOutside);
            return () => document.removeEventListener('click', handleClickOutside);
        }
    }, [showChatHistory]);

    return (
        <>
            <header className={`header ${showChatHistory ? 'sidebar-open' : ''}`}>
                <div className="header-left">
                    <img className="header-logo" src={logo} alt="T-J logo" />
                    <nav className="header-icons">
                        <img
                            className="chats-icon"
                            src={updated}
                            alt="chats icon"
                            onClick={toggleChatHistory}
                            style={{ cursor: 'pointer' }}
                        />
                        <img
                            className="plus-icon"
                            src={plus}
                            alt="plus icon"
                        />
                    </nav>
                </div>

                <div className="header-description">
                    <h1 className="current-chat">
                        {chats.find(c => c.id === currentChatId)?.title || "Чат"}
                    </h1>
                </div>

                <img
                    className="question-icon"
                    src={questionIcon}
                    alt="question icon"
                    onClick={toggleHelp}
                    style={{ cursor: 'pointer' }}
                />
            </header>

            {showChatHistory && (
                <div className="chat-history-sidebar">
                    <div className="chat-history-content-wrapper" onClick={(e) => e.stopPropagation()}>
                        <div className="chat-history-header">
                            <img className="chats-logo" src={logo} alt="T-J logo" />
                            <h2 className="chat-history-title">Т-Ж Ассистент</h2>
                            <img
                                className="close-chats-icon"
                                src={updated}
                                alt="chats icon"
                                style={{ cursor: 'pointer' }}
                                onClick={closeChatHistory}
                            />
                        </div>
                        <div className="chat-history-content">
                            <button
                                className="new-chat"
                                onClick={handleCreateNewChat}
                            >
                                <img className="new-plus" src={plus} alt="Создать" />
                                <span className="new-chat-text">Новый чат</span>
                            </button>
                            <div className="chat-history-list">
                                {chats.map(chat => (
                                    <div
                                        key={chat.id}
                                        className={`chat-history-item ${currentChatId === chat.id ? 'active' : ''}`}
                                        onClick={() => onSelectChat(chat.id)}  // ← выбор чата
                                    >
                                        <h4>{chat.title}</h4>
                                        <button
                                            className="chat-history-points"
                                            onClick={(e) => handleChatPointsClick(chat.id, e)}
                                        >
                                            <span>...</span>
                                        </button>

                                        {activeChatMenu === chat.id && (
                                            <div className="chat-context-menu">
                                                <button
                                                    className="chat-menu-rename"
                                                    onClick={() => handleRenameChat(chat.id)}
                                                >
                                                    Переименовать
                                                </button>
                                                <button
                                                    className="chat-menu-delete"
                                                    onClick={() => handleDeleteChat(chat.id)}
                                                >
                                                    Удалить
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="nickname-button">
                                <img className="profile-icon" src={profilelogo} alt="Профиль" />
                                <span className="nick">{nickname}</span>
                                <button
                                    className="nickname-points"
                                    onClick={handleProfilePointsClick}
                                >
                                    <span>...</span>
                                </button>

                                {showProfileMenu && (
                                    <div className="profile-context-menu">
                                        <button className="profile-menu-settings">
                                            Настройки
                                        </button>
                                        <button
                                            className="profile-menu-logout"
                                            onClick={handleLogoutClick}
                                        >
                                            Выйти
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {showHelp && (
                <div className="help-overlay">
                    <div className="help-modal">
                        <button className="help-close-button" onClick={closeHelp}>
                            ×
                        </button>
                        <div className="help-header">
                            <h2 className="help-title">Помощь по ассистенту Т-Ж</h2>
                        </div>
                        <div className="help-content">
                            <h3 className="help-description-title">Общая информация</h3>
                            <p className="help-description">
                                Ассистент помогает находить ответы в статьях Т-Ж.<br />
                                Задавайте вопросы — он проанализирует архив и даст точный ответ со ссылками на источники.
                            </p>
                            <h3 className="help-description-title">Основные функции</h3>
                            <ul className="help-features">
                                <li><strong>Умный поиск</strong> — анализирует тысячи статей Т-Ж</li>
                                <li><strong>Контекст диалога</strong> — помнит предыдущие вопросы в беседе</li>
                                <li><strong>Проверенные источники</strong> — все ответы со ссылками на статьи</li>
                                <li><strong>Мультитематичность</strong> — финансы, инвестиции, право, путешествия, карьера, быт</li>
                            </ul>
                            <h3 className="help-description-title">Частые вопросы</h3>
                            <div className="help-faq">
                                <div className="faq-item">
                                    <strong className="gaq-text">—Как правильно задавать вопросы?<br />
                                        Будьте конкретны: вместо "про налоги" — "какие налоги у самозанятых?"<br />
                                        <br />
                                        —На каких статьях основаны ответы?<br />
                                        На всем архиве Т-Ж с 2010 года. База обновляется ежедневно.<br />
                                        <br />
                                        —Сколько стоит использование?<br />
                                        Абсолютно бесплатно. Никаких подписок и скрытых платежей.<br />
                                        <br />
                                        —Что делать, если ответ не найден?<br />
                                        Попробуйте переформулировать вопрос или выберите одну из предложенных смежных тем.<br />
                                        <br />
                                        —Можно ли доверять ответам?<br />
                                        Все ответы основаны на проверенных статьях Т-Ж с указанием источников.
                                    </strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}