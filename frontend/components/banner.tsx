import styles from "./banner.module.css";

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

export default Banner;
