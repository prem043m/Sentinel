from app.utils.logger import setup_logger


def main():
    logger = setup_logger()

    logger.info("=" * 50)
    logger.info("Starting SentinelAI...")
    logger.info("Foundation initialized successfully.")
    logger.info("=" * 50)

    print("SentinelAI is running.")


if __name__ == "__main__":
    main()