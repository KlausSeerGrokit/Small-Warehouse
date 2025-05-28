import React from 'react';
import styles from './FinalizeTote.module.scss';

interface FinalizeToteProps {
  onSendCommand: () => void;
  disabled: boolean;
}

const FinalizeTote: React.FC<FinalizeToteProps> = ({ onSendCommand, disabled }) => {
  const handleSendCommand = () => {
    onSendCommand()
  };
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Inspect Tote</h1>
      <button disabled={disabled} onClick={handleSendCommand} className={styles.sendButton}>
        Remove Tote
      </button>
    </div>
  );
};

export default FinalizeTote;
