import React, { useState, useEffect } from "react";
import logo from "../assets/images/robot.png";

export default function Registration({ onLogin, onRegister }) {
    const [isRegistration, setIsRegistration] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordRepeat, setPasswordRepeat] = useState("");
    const [isEmailValid, setIsEmailValid] = useState(true);
    const [emailError, setEmailError] = useState("");
    const [passwordError, setPasswordError] = useState("");
    const [isFormValid, setIsFormValid] = useState(false); // Изменено на false по умолчанию
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        validateForm();
    }, [email, password, passwordRepeat, isRegistration]);

    const handleRegistrationClick = () => {
        setIsRegistration(true);
        setPasswordError("");
        setPasswordRepeat(""); // Сброс повторного пароля
    };

    const handleSignInClick = () => {
        setIsRegistration(false);
        setPasswordError("");
        setPasswordRepeat(""); // Сброс повторного пароля
    };

    const handleEmailChange = (e) => {
        const value = e.target.value;
        setEmail(value);

        if (value === "") {
            setIsEmailValid(true);
            setEmailError("");
        } else {
            const isValid = validateEmail(value);
            setIsEmailValid(isValid);
            if (!isValid) {
                setEmailError("Введите корректный email");
            } else {
                setEmailError("");
            }
        }
    };

    const handlePasswordChange = (e) => {
        const value = e.target.value;
        setPassword(value);

        if (passwordError && isRegistration && value === passwordRepeat) {
            setPasswordError("");
        }
    };

    const handlePasswordRepeatChange = (e) => {
        const value = e.target.value;
        setPasswordRepeat(value);

        if (passwordError && value === password) {
            setPasswordError("");
        }
    };

    const handleEmailBlur = (e) => {
        const value = e.target.value;
        if (value !== email) {
            setEmail(value);
        }
    };

    const handlePasswordBlur = (e) => {
        const value = e.target.value;
        if (value !== password) {
            setPassword(value);
        }
    };

    const handlePasswordRepeatBlur = (e) => {
        const value = e.target.value;
        if (value !== passwordRepeat) {
            setPasswordRepeat(value);
        }
    };

    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };

    const validateForm = () => {
        const emailValid = validateEmail(email);
        setIsEmailValid(emailValid);

        if (!emailValid && email) {
            setEmailError("Введите корректный email");
        } else {
            setEmailError("");
        }

        if (isRegistration) {
            const passwordsNotEmpty = password && passwordRepeat;
            const passwordsMatch = password === passwordRepeat;
            const passwordValid = password.length >= 6;

            if (passwordsNotEmpty && !passwordsMatch) {
                setPasswordError("Пароли не совпадают");
            } else if (password && password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
            } else {
                setPasswordError("");
            }

            setIsFormValid(emailValid && passwordsNotEmpty && passwordsMatch && passwordValid);
        } else {
            const passwordValid = password.length >= 6;

            if (password && password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
            } else {
                setPasswordError("");
            }

            setIsFormValid(emailValid && passwordValid);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        validateForm();

        if (!isFormValid) {
            return;
        }

        setIsLoading(true);

        if (isRegistration) {
            if (password !== passwordRepeat) {
                setPasswordError("Пароли не совпадают");
                setIsLoading(false);
                return;
            }

            if (password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
                setIsLoading(false);
                return;
            }
        } else {
            if (password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
                setIsLoading(false);
                return;
            }
        }

        try {
            let success;
            if (isRegistration) {
                success = await onRegister(email, password);
            } else {
                success = await onLogin(email, password);
            }

            if (!success) {
                alert("Ошибка авторизации. Проверьте email и пароль.");
            }
        } catch (error) {
            console.error("Ошибка:", error);
            alert(error.message || "Произошла ошибка. Попробуйте еще раз.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <main className='registration-main'>
            <form onSubmit={handleSubmit}>
                <div
                    id='registration-form'
                    className={`registration-form ${!isRegistration ? 'no-account' : ''}`}
                    style={{ height: isRegistration ? '472px' : '384px' }}
                >
                    <div id='sign-type' className='sign-type'>
                        <button
                            type="button"
                            id='signin-button'
                            className={`signin-button ${!isRegistration ? 'active' : ''}`}
                            onClick={handleSignInClick}
                            disabled={isLoading}
                        >
                            Вход
                        </button>
                        <button
                            type="button"
                            id='reg-button'
                            className={`reg-button ${isRegistration ? 'active' : ''}`}
                            onClick={handleRegistrationClick}
                            disabled={isLoading}
                        >
                            Регистрация
                        </button>
                    </div>

                    <input
                        id='email-input'
                        className={`email-input ${!isEmailValid && email ? 'invalid' : ''}`}
                        placeholder='Введите Email'
                        type="email"
                        value={email}
                        onChange={handleEmailChange}
                        onBlur={handleEmailBlur} // Добавлен onBlur
                        required
                        disabled={isLoading}
                        autoComplete="email"
                    />
                    {!isEmailValid && emailError && (
                        <div className="error-message">{emailError}</div>
                    )}

                    <input
                        id='password-input'
                        className={`password-input ${passwordError ? 'invalid' : ''}`}
                        placeholder='Введите пароль'
                        type="password"
                        value={password}
                        onChange={handlePasswordChange}
                        onBlur={handlePasswordBlur} // Добавлен onBlur
                        required
                        disabled={isLoading}
                        autoComplete={isRegistration ? "new-password" : "current-password"}
                    />

                    {isRegistration && (
                        <input
                            id='password-input-repeat'
                            className={`password-input-repeat ${passwordError ? 'invalid' : ''}`}
                            placeholder='Повторите пароль'
                            type="password"
                            value={passwordRepeat}
                            onChange={handlePasswordRepeatChange}
                            onBlur={handlePasswordRepeatBlur} // Добавлен onBlur
                            required
                            disabled={isLoading}
                            autoComplete="new-password"
                        />
                    )}

                    {passwordError && (
                        <div className="error-message">{passwordError}</div>
                    )}

                    <button
                        id='sign-in-button'
                        className='sign-in-button'
                        type="submit"
                        disabled={!isFormValid || isLoading}
                    >
                        {isLoading ? 'Загрузка...' : isRegistration ? 'Зарегистрироваться' : 'Войти'}
                    </button>

                    <img
                        id='robot-circle-flat-icon'
                        className='robot-circle-flat-icon'
                        src={logo}
                        alt="Ассистент Т-Ж"
                    />

                    <div id='assistant-text-logo' className='assistant-text-logo'>
                        Ассистент Т-Ж
                    </div>
                </div>
            </form>
        </main>
    );
}