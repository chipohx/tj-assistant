import React, { useState } from "react";
import robotIcon from "../assets/images/robot.png";

export default function Registration({ onLogin }) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        const endpoint = isLogin ? "/auth/login" : "/auth/register";
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Ошибка авторизации");
            }

            const data = await response.json();

            if (isLogin) {
                localStorage.setItem("auth_token", data.access_token);
                onLogin();
            } else {
                alert("Регистрация успешна! Проверьте email для подтверждения.");
                setIsLogin(true);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <img className="auth-logo" src={robotIcon} alt="T-J Assistant" />
                <h2 className="auth-title">{isLogin ? "Вход" : "Регистрация"}</h2>

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="example@mail.ru"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Пароль</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="Введите пароль"
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button
                        type="submit"
                        className="auth-button"
                        disabled={loading}
                    >
                        {loading ? "Загрузка..." : (isLogin ? "Войти" : "Зарегистрироваться")}
                    </button>
                </form>

                <div className="auth-switch">
                    <p>
                        {isLogin ? "Нет аккаунта? " : "Уже есть аккаунт? "}
                        <button
                            type="button"
                            className="switch-button"
                            onClick={() => {
                                setIsLogin(!isLogin);
                                setError("");
                            }}
                        >
                            {isLogin ? "Зарегистрироваться" : "Войти"}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}