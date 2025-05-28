import React, { useState } from 'react';
import styles from './ToteDesignation.module.scss';
import classNames from 'classnames';

interface ToteDesignationProps {
  onSendCommand: (status: 'Good' | 'Bad') => void;
}

const ToteDesignation: React.FC<ToteDesignationProps> = ({ onSendCommand }) => {
  const [status, setStatus] = useState<'Good' | 'Bad' | null>(null);

  const handleStatusChange = (newStatus: 'Good' | 'Bad') => {
    setStatus(newStatus);
    onSendCommand(newStatus)
  };


  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Tote Designation</h1>
      <div className={styles.buttonContainer}>
        <button
          onClick={() => handleStatusChange('Good')}
          className={classNames(styles.button, styles.good, {
            [styles.outline]: status === 'Good',
          })}
        >
          Good
        </button>
        <button
          onClick={() => handleStatusChange('Bad')}
          className={classNames(styles.button, styles.bad, {
            [styles.outline]: status === 'Bad',
          })}
        >
          Bad
        </button>
      </div>
      {/* Uncomment the following button if needed */}
      {/* <button onClick={handleSendCommand} className={styles.sendButton}>
        Send Command
      </button> */}
    </div>
  );
};

export default ToteDesignation;
