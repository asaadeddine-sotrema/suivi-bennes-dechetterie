import { createContext, useCallback, useContext, useState } from "react";
import Icon from "./Icon";

const ToastContext = createContext(null);

let _id = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const remove = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const notify = useCallback((message, type = "success", duree = 3500) => {
    const id = ++_id;
    setToasts((t) => [...t, { id, message, type }]);
    if (duree) setTimeout(() => remove(id), duree);
  }, [remove]);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`} onClick={() => remove(t.id)} role="status">
            <Icon name={t.type === "error" ? "x" : "check"} size={16} />
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

/** Renvoie la fonction notify(message, type?, duree?). type ∈ {success, error}. */
export function useToast() {
  const ctx = useContext(ToastContext);
  return ctx ?? (() => {});
}
