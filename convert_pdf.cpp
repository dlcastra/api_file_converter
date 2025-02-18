#include <iostream>
#include <Magick++.h>
#include <fstream>
#include <poppler/cpp/poppler-document.h>
#include <poppler/cpp/poppler-page.h>
#include <unordered_map>
#include <unordered_set>
#include <functional>

// Convert PDF to Image
// Convert PDF to Image
int pdf2img(const std::string &input_pdf, const std::string &output_file) {
    try {
        // Initialize ImageMagick
        Magick::InitializeMagick(nullptr);

        // Supported image formats
        static const std::unordered_set<std::string> valid_image_extensions = {
            ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"
        };

        // Check if the output file extension is valid
        std::string extension = output_file.substr(output_file.rfind('.'));
        if (valid_image_extensions.find(extension) == valid_image_extensions.end()) {
            std::cerr << "Invalid image file format. Supported formats: jpg, jpeg, png, bmp, tiff, gif.\n";
            return 1;
        }

        // Load the first page of the PDF
        Magick::Image image(input_pdf + "[0]");

        // Set format (ensure the output extension is valid)
        image.magick(extension.substr(1));

        // Strip any profiles that may cause issues
        image.strip();

        // Force RGB color space and explicitly convert to RGB if grayscale
        if (image.type() == Magick::GrayscaleType) {
            image.type(Magick::TrueColorType);  // Convert to RGB
        }

        // Optionally, force the colorspace (to RGB)
        image.colorSpace(Magick::RGBColorspace);

        // Write the image to the output file
        image.write(output_file);

        std::cout << "PDF successfully converted to image: " << output_file << "\n";
    } catch (Magick::Exception &error) {
        std::cerr << "Error: " << error.what() << std::endl;
        return 1;
    }

    return 0;
}


// Convert PDF to Text
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

// Format to function map
std::unordered_map<std::string, std::function<int(const std::string&, const std::string&)>> format_map = {
    {".jpg", pdf2img}, {".jpeg", pdf2img}, {".png", pdf2img}, {".bmp", pdf2img}, {".tiff", pdf2img}, {".gif", pdf2img},
    {".txt", pdf2txt}, {".docx", pdf2txt}, {".odt", pdf2txt}
};

int main(int argc, char *argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <format_to> <input_pdf> <output_file>\n";
        return 1;
    }

    std::string format_to = argv[1];
    std::string input_pdf = argv[2];
    std::string output_file = argv[3];

    // Extract file extension from output file
    std::string extension = output_file.substr(output_file.rfind('.'));

    // Check if the extension is valid and call the appropriate function
    auto it = format_map.find(extension);
    if (it != format_map.end()) {
        return it->second(input_pdf, output_file);
    } else {
        std::cerr << "Unsupported file format. Supported formats: .txt, .docx, .odt, .jpg, .jpeg, .png, .bmp, .tiff, .gif.\n";
        return 1;
    }
}
