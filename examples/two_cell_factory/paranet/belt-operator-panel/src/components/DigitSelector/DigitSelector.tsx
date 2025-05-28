import React from "react";
import classNames from "classnames";
import styles from "./DigitSelector.module.scss";

interface DigitSelectorProps {
  digitSelected: string;
  onSelectDigit: (digit: string) => void;
}

const DigitSelector: React.FC<DigitSelectorProps> = ({
  digitSelected,
  onSelectDigit,
}) => {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Digit Selector</h1>
      <div className={styles.digitSelector}>
        <button
          onClick={() => onSelectDigit("10")}
          className={classNames(styles.button, {
            [styles.selected]: digitSelected === "10",
          })}
        >
          10
        </button>
        <button
          onClick={() => onSelectDigit("11")}
          className={classNames(styles.button, {
            [styles.selected]: digitSelected === "11",
          })}
        >
          11
        </button>
      </div>
    </div>
  );
};

export default DigitSelector;
