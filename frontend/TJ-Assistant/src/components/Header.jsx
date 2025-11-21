import React, { useState } from "react";
import logo from "../assets/images/t-j.png";
import questionIcon from "../assets/images/question.png";
import profileIcon from "../assets/images/account.png";

export default function Header() {
    const [showHelp, setShowHelp] = useState(false);

    const toggleHelp = () => {
        setShowHelp(!showHelp);
    };

    const closeHelp = () => {
        setShowHelp(false);
    };

    return (
        <>
            <header className="header">
                <img className="header-logo" src={logo} alt="T-J logo" />
                <div className="header-description">
                    <h1 className="assistant-tj">Ассистент Т-Ж</h1>
                    <a className="ai-expert">AI-эксперт по статьям</a>
                </div>
                <nav className="header-icons">
                    <img
                        className="question-icon"
                        src={questionIcon}
                        alt="question icon"
                        onClick={toggleHelp}
                        style={{ cursor: 'pointer' }}
                    />
                    <img
                        className="profile-icon"
                        src={profileIcon}
                        alt="profile icon"
                    />
                </nav>
            </header>

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