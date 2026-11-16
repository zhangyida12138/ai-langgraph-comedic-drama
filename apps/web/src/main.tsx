import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("#root 容器缺失：检查 index.html");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
