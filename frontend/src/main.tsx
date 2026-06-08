import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Compare from "./pages/Compare";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Launcher from "./pages/Launcher";
import Leaderboard from "./pages/Leaderboard";
import RunDetail from "./pages/RunDetail";
import TestDetail from "./pages/TestDetail";
import Tests from "./pages/Tests";
import "./i18n";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/launcher" element={<Launcher />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/runs/:runId" element={<RunDetail />} />
          <Route path="/tests" element={<Tests />} />
          <Route path="/tests/:suite" element={<TestDetail />} />
          <Route path="/compare" element={<Compare />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
