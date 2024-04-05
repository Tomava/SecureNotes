import styles from "./banner.module.scss";

type BannerProps = {
  text: string;
};

const Banner: React.FC<BannerProps> = ({ text }) => {
  return (
    <div className={styles.banner}>
      {text}
    </div>
  );
};

const ErrorBanner: React.FC<BannerProps> = ({ text }) => {
  return (
    <div className={styles.errorBanner}>
      {text}
    </div>
  );
};

export {Banner, ErrorBanner};
