"use strict";

const API_BASE = "";

function getToken() {
  return localStorage.getItem("access_token") || "";
}

function setToken(token) {
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

function redirectToLogin() {
  window.location.href = "/app/login.html";
}

function requireAuth() {
  if (!getToken()) {
    redirectToLogin();
  }
}

function setText(targetId, text) {
  const el = document.getElementById(targetId);
  if (!el) return;
  el.textContent = text;
}

function showError(targetId, message) {
  setText(targetId, message || "오류가 발생했습니다.");
}

function showInfo(targetId, message) {
  setText(targetId, message || "");
}

async function apiFetch(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  if (!headers.Authorization) {
    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  const response = await fetch(API_BASE + path, { ...options, headers });
  if (response.status === 401) {
    setToken("");
    redirectToLogin();
    throw new Error("Unauthorized");
  }
  return response;
}

function parseIntegerList(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item !== "")
    .map((item) => Number(item))
    .filter((num) => Number.isFinite(num));
}

function joinIntegerList(list) {
  if (!Array.isArray(list)) return "";
  return list.join(", ");
}

function parseNumber(value) {
  if (value === "" || value === null || value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function safeJson(value) {
  try {
    return JSON.parse(value);
  } catch (err) {
    return null;
  }
}
