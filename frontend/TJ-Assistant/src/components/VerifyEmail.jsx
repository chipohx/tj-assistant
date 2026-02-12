import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import logo from "../assets/images/robot.png";

export default function VerifyEmail() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('verifying');
    const [message, setMessage] = useState('');

    const API_BASE_URL = "http://localhost:8000/api";

    useEffect(() => {
        const verifyEmail = async () => {
            const token = searchParams.get('token');
            
            if (!token) {
                setStatus('error');
                setMessage('Токен верификации не найден');
                setTimeout(() => navigate('/'), 3000);
                return;
            }

            try {
                const response = await fetch(
                    `${API_BASE_URL}/auth/verify-email?token=${encodeURIComponent(token)}`,
                    {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    }
                );

                const data = await response.json();

                if (response.ok) {
                    setStatus('success');
                    setMessage('Email успешно подтвержден! Теперь вы можете войти в аккаунт.');
                    setTimeout(() => navigate('/'), 3000);
                } else {
                    setStatus('error');
                    setMessage(data.detail || 'Ошибка подтверждения email');
                    setTimeout(() => navigate('/'), 3000);
                }
            } catch (error) {
                console.error('Ошибка верификации:', error);
                setStatus('error');
                setMessage('Произошла ошибка при подтверждении email');
                setTimeout(() => navigate('/'), 3000);
            }
        };

        verifyEmail();
    }, [searchParams, navigate]);

    return (
        <main className='registration-main'>
            <div className='verify-email-container'>
                <img className='verify-logo' src={logo} alt="Ассистент Т-Ж" />
                
                {status === 'verifying' && (
                    <>
                        <h2 className='verify-title'>Подтверждение email</h2>
                        <div className="loading-dots verify-loading">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <p className='verify-message'>Проверяем ваш токен...</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <h2 className='verify-title success'>✓ Успешно!</h2>
                        <p className='verify-message success'>{message}</p>
                        <p className='verify-redirect'>Перенаправление на страницу входа...</p>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <h2 className='verify-title error'>✗ Ошибка</h2>
                        <p className='verify-message error'>{message}</p>
                        <p className='verify-redirect'>Перенаправление на главную...</p>
                    </>
                )}
            </div>
        </main>
    );
}