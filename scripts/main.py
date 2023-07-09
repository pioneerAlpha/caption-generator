import extract_data_from_card as edfc
import output_generator as og
import time
import os


def main():
    
    
    whisper_model = og.get_model("small")

    while True:
        edfc.main(whisper_model)
        time.sleep(20)
        # break


if __name__ == "__main__":
    main()