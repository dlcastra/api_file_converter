#include <iostream>
#include <fstream>
#include <poppler/cpp/poppler-document.h>
#include <poppler/cpp/poppler-page.h>
int main(int argc, char *argv[]) {
    if (argc != 3){
	std::cerr << "Usage: " << argv[0] << "<input_pdf> <output_txt>\n";
	return 1;
}
    std::string input_pdf = argv[1];
    std::string output_txt = argv[2];
    poppler::document* doc = poppler::document::load_from_file(input_pdf);
    if (!doc) {
        std::cerr << "Error occurred while opening PDF: " << input_pdf << "\n";
        return 1;
    }

    std::ofstream output(output_txt);
    if (!output.is_open()) {
        std::cerr << "Error occurred while opening output file: " << output_txt << "\n";
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

