import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import App from "./App.jsx";
import VerifyEmail from "./components/VerifyEmail.jsx";

import "./assets/styles/fonts.css";
import "./assets/styles/global.css";
import "./assets/styles/style.css";

console.log("Main.jsx loaded"); // Проверка

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/activate" element={<VerifyEmail />} />
                <Route path="/" element={<App />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    </React.StrictMode>
);