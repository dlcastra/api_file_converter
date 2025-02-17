#include <iostream>
#include <Magick++.h>
#include <fstream>
#include <poppler/cpp/poppler-document.h>
#include <poppler/cpp/poppler-page.h>

int pdf2img(const std::string &input_pdf, const std::string &output_file) {
    Magick::InitializeMagick(nullptr);  // Corrected namespace
    try {
        Magick::Image image(input_pdf + "[0]");  // Load the first page
        image.write(output_file);  // Write image to output file

        std::cout << "Conversion ended!\n";
    } catch (Magick::Exception &error) {
        std::cerr << "Error: " << error.what() << std::endl;
        return 1;
    }
    return 0;
}

int pdf2txt(const std::string &input_pdf, const std::string &output_file) {
    poppler::document* doc = poppler::document::load_from_file(input_pdf);
    if (!doc) {
        std::cerr << "Error occurred while opening PDF: " << input_pdf << "\n";
        return 1;
    }

    std::ofstream output(output_file);  // Corrected the variable name here
    if (!output.is_open()) {
        std::cerr << "Error occurred while opening output file: " << output_file << "\n";
        return 1;
    }

    int num_pages = doc->pages();
    for (int i = 0; i < num_pages; ++i) {
        poppler::page* p = doc->create_page(i);
        poppler::ustring utext = p->text();
        std::string text(utext.begin(), utext.end());

        output << text << "\n\n";
    }

    std::cout << "PDF successfully converted to text!\n";
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <format_to> <input_pdf> <output_file>\n";
        return 1;
    }

    std::string format_to = argv[1];
    std::string input_pdf = argv[2];
    std::string output_file = argv[3];

    if (format_to == "img") {
        return pdf2img(input_pdf, output_file);
    } else if (format_to == "txt") {
        return pdf2txt(input_pdf, output_file);
    } else {
        std::cerr << "Invalid format specified.\n";
        return 1;
    }

    return 0;
}
