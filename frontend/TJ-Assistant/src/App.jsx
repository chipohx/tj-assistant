import React, { useState, useEffect } from "react";
import Header from "./components/Header.jsx";
import Main from "./components/Main.jsx";
import Registration from "./components/Registration.jsx";

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("authToken");
        if (token) {
            setIsLoggedIn(true);
        }
    }, []);

    const handleLogin = () => {
        setIsLoggedIn(true);
        localStorage.setItem("authToken", "example-token");
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        localStorage.removeItem("authToken");
    };

    return (
        <>
            {isLoggedIn ? (
                <>
                    <Header onLogout={handleLogout} />
                    <Main />
                </>
            ) : (
                <Registration onLogin={handleLogin} />
            )}
        </>
    );
}

export default App;