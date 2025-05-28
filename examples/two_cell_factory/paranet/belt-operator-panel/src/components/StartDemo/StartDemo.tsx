import React from "react";
import styles from "./StartDemo.module.scss";

interface StartDemoProps {
  onSendCommand: () => void;
  disabled: boolean;
}

const StartDemo: React.FC<StartDemoProps> = ({ onSendCommand, disabled }) => {
  const handleSendCommand = () => {
    onSendCommand();
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Start Demo</h1>
      <button
        disabled={disabled}
        onClick={handleSendCommand}
        className={styles.sendButton}
      >
        Place Tote
      </button>
    </div>
  );
};

export default StartDemo;
