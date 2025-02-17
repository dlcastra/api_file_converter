#include <iostream>
#include <Magick++.h>

using namespace Magick;

int main(int argc, char *argv[]) {

    if(argc != 3){
	std::cerr<< "Usage: " << argv[0] << "<input_pdf> <output_jpeg>\n";
	return 1;	
	}
    InitializeMagick(nullptr);
    try {
	std::string input_pdf = argv[1];
	std::string  output_jpeg = argv[2];
        Image image(input_pdf + "[0]");
        image.write(output_jpeg);

        std::cout << "Convertion ended!\n";
    } catch (Exception &error) {
        std::cerr << "Error: " << error.what() << std::endl;
    }
    return 0;
}
