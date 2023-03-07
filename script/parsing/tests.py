from parsing.log import logger

if __name__ == '__main__':
    try:
        print(1)
        s = 1/0
    except Exception as e:
        logger.info("ошибка", exc_info=True)

    print(2)
