import React, { useState } from "react";
import logo from "../assets/images/robot.png";
import questionIcon from "../assets/images/question.png";
import chats from "../assets/images/chats.png";
import plus from "../assets/images/plus.png";
import profilelogo from "../assets/images/account.png";

export default function Header() {
    const [showHelp, setShowHelp] = useState(false);
    const [showChatHistory, setShowChatHistory] = useState(false);

    const toggleHelp = () => {
        setShowHelp(!showHelp);
    };

    const closeHelp = () => {
        setShowHelp(false);
    };

    const toggleChatHistory = () => {
        setShowChatHistory(!showChatHistory);
    };

    const closeChatHistory = () => {
        setShowChatHistory(false);
    };

    return (
        <>
            <header className="header">
                <img className="header-logo" src={logo} alt="T-J logo" />
                <nav className="header-icons">
                    <img
                        className="chats-icon"
                        src={chats}
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
                <div className="header-description">
                    <h1 className="assistant-tj">Ассистент Т-Ж</h1>
                    <a className="ai-expert">AI-эксперт по статьям</a>
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
                <div className="chat-history-overlay" onClick={closeChatHistory}>
                    <div className="chat-history-sidebar" onClick={(e) => e.stopPropagation()}>
                        <div className="chat-history-header">
                            <img className="chats-logo" src={logo} alt="T-J logo" />
                            <h2 className="chat-history-title">Т-Ж Ассистент</h2>
                            <img
                                className="close-chats-icon"
                                src={chats}
                                alt="chats icon"
                                style={{ cursor: 'pointer' }}
                                onClick={closeChatHistory}
                            />
                        </div>
                        <div className="chat-history-content">
                            <button className="new-chat">
                                <img className="new-plus" src={plus} alt="Создать" />
                                <span className="new-chat-text">Новый чат</span>
                            </button>
                            <div className="chat-history-list">

                                <div className="chat-history-item">
                                    <h4>Чат 5</h4>
                                    <span className="chat-history-points">...</span>
                                </div>

                                <div className="chat-history-item">
                                    <h4>Чат 4</h4>
                                    <span className="chat-history-points">...</span>
                                </div>

                                <div className="chat-history-item">
                                    <h4>Чат 3</h4>
                                    <span className="chat-history-points">...</span>
                                </div>

                                <div className="chat-history-item">
                                    <h4>Чат 2</h4>
                                    <span className="chat-history-points">...</span>
                                </div>

                                <div className="chat-history-item">
                                    <h4>Чат 1</h4>
                                    <span className="chat-history-points">...</span>
                                </div>
                            </div>
                            <button className="nickname-button">
                                <img className="profile-icon" src={profilelogo} alt="Профиль" />
                                <span className="nick">Никнейм</span>
                                <span className="nickname-points">...</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showHelp && (
                <div className="help-overlay">
                    <div className="help-modal">
                        <div className="help-header">
                            <h2 className="help-title">Помощь по ассистенту Т-Ж</h2>
                            <button className="help-close-button" onClick={closeHelp}>
                                ×
                            </button>
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