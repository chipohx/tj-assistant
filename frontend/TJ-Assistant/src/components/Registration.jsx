import React, { useState } from "react";
import logo from "../assets/images/robot.png";

export default function Registration({ onLogin, onRegister }) {
    const [isRegistration, setIsRegistration] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordRepeat, setPasswordRepeat] = useState("");
    const [isEmailValid, setIsEmailValid] = useState(true);
    const [emailError, setEmailError] = useState("");
    const [passwordError, setPasswordError] = useState("");
    const [isFormValid, setIsFormValid] = useState(true);
    const [isLoading, setIsLoading] = useState(false);

    const handleRegistrationClick = () => {
        setIsRegistration(true);
        setPasswordError("");
        setIsFormValid(true);
    };

    const handleSignInClick = () => {
        setIsRegistration(false);
        setPasswordError("");
        setIsFormValid(true);
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
        validateForm();
    };

    const handlePasswordChange = (e) => {
        const value = e.target.value;
        setPassword(value);
        if (isRegistration && passwordRepeat && value !== passwordRepeat) {
            setPasswordError("Пароли не совпадают");
        } else {
            setPasswordError("");
        }
        validateForm();
    };

    const handlePasswordRepeatChange = (e) => {
        const value = e.target.value;
        setPasswordRepeat(value);

        if (isRegistration) {
            if (password && value !== password) {
                setPasswordError("Пароли не совпадают");
            } else {
                setPasswordError("");
            }
        }
        validateForm();
    };

    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };

    const validateForm = () => {
        if (isRegistration) {
            const emailValid = validateEmail(email);
            const passwordsMatch = password === passwordRepeat;
            const passwordsNotEmpty = password && passwordRepeat;

            setIsFormValid(emailValid && passwordsMatch && passwordsNotEmpty);
        } else {
            const emailValid = validateEmail(email);
            const passwordNotEmpty = password.length > 0;

            setIsFormValid(emailValid && passwordNotEmpty);
        }
    };


    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        if (!validateEmail(email)) {
            setIsEmailValid(false);
            setEmailError("Введите корректный email");
            setIsLoading(false);
            return;
        }

        if (isRegistration) {
            if (password !== passwordRepeat) {
                setPasswordError("Пароли не совпадают");
                setIsFormValid(false);
                setIsLoading(false);
                return;
            }

            if (password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
                setIsFormValid(false);
                setIsLoading(false);
                return;
            }
        }

        if (!isRegistration && password.length < 6) {
            setPasswordError("Пароль должен быть не менее 6 символов");
            setIsFormValid(false);
            setIsLoading(false);
            return;
        }

        console.log("Email:", email);
        console.log("Password:", password);

        try {
            let success;
            if (isRegistration) {
                console.log("Регистрация нового пользователя");
                success = await onRegister(email, password);
            } else {
                console.log("Вход пользователя");
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
                        className={`email-input ${!isEmailValid ? 'invalid' : ''}`}
                        placeholder='Введите Email'
                        type="email"
                        value={email}
                        onChange={handleEmailChange}
                        required
                        disabled={isLoading}
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
                        required
                        disabled={isLoading}
                    />

                    {isRegistration && (
                        <input
                            id='password-input-repeat'
                            className={`password-input-repeat ${passwordError ? 'invalid' : ''}`}
                            placeholder='Повторите пароль'
                            type="password"
                            value={passwordRepeat}
                            onChange={handlePasswordRepeatChange}
                            required
                            disabled={isLoading}
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