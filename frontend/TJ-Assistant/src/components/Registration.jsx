import React, { useState } from "react";
import logo from "../assets/images/robot.png";

export default function Registration({ onLogin }) {
    const [isRegistration, setIsRegistration] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordRepeat, setPasswordRepeat] = useState("");
    const [isEmailValid, setIsEmailValid] = useState(true);
    const [emailError, setEmailError] = useState("");
    const [passwordError, setPasswordError] = useState("");
    const [isFormValid, setIsFormValid] = useState(true);

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

    const handleSubmit = (e) => {
        e.preventDefault();

        if (!validateEmail(email)) {
            setIsEmailValid(false);
            setEmailError("Введите корректный email");
            return;
        }

        if (isRegistration) {
            if (password !== passwordRepeat) {
                setPasswordError("Пароли не совпадают");
                setIsFormValid(false);
                return;
            }

            if (password.length < 6) {
                setPasswordError("Пароль должен быть не менее 6 символов");
                setIsFormValid(false);
                return;
            }
        }

        if (!isRegistration && password.length < 6) {
            setPasswordError("Пароль должен быть не менее 6 символов");
            setIsFormValid(false);
            return;
        }

        console.log("Email:", email);
        console.log("Password:", password);
        if (isRegistration) {
            console.log("Регистрация нового пользователя");
        } else {
            console.log("Вход пользователя");
        }

        setTimeout(() => {
            onLogin();
        }, 500);
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
                        >
                            Вход
                        </button>
                        <button
                            type="button"
                            id='reg-button'
                            className={`reg-button ${isRegistration ? 'active' : ''}`}
                            onClick={handleRegistrationClick}
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
                        />
                    )}

                    {passwordError && (
                        <div className="error-message">{passwordError}</div>
                    )}

                    <button
                        id='sign-in-button'
                        className='sign-in-button'
                        type="submit"
                        disabled={!isFormValid}
                    >
                        {isRegistration ? 'Зарегистрироваться' : 'Войти'}
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