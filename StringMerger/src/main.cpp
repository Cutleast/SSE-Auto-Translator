#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct StringEntry {
	std::string editor_id;
	std::string type;
	std::string original;
	std::string translated;
	std::optional<int> index;
};

int main(int argc, char* argv[]) {
	if (argc != 3) {
		std::cerr << "Usage: " << argv[0] << " <Path to original strings json> <Path to translated strings json>" << std::endl;
		return 1;
	}

	std::string originalPath = argv[1];
	std::string translatedPath = argv[2];

	try {
		std::ifstream originalFile(originalPath), translatedFile(translatedPath);

		if (!originalFile.is_open() || !translatedFile.is_open()) {
			std::cerr << "Error: Unable to open input files." << std::endl;
			return 1;
		}

		json originalJson, translatedJson;
		originalFile >> originalJson;
		translatedFile >> translatedJson;

		std::unordered_map<std::string, StringEntry> entries;
		entries.reserve(originalJson.size());

		//Add the original data to the map and initialize the translation with the original value
		for (const auto& entry : originalJson) {
			StringEntry stringEntry;
			stringEntry.editor_id = entry["editor_id"];
			stringEntry.type = entry["type"];
			stringEntry.original = entry["string"];
			stringEntry.translated = ""; //Initialize with empty string
			if (!entry["index"].is_null()) {
				stringEntry.index = entry["index"].get<int>(); //Store as integer
			}
			entries.emplace(stringEntry.editor_id + "_" + (stringEntry.index ? std::to_string(*stringEntry.index) : "null") + "_" + stringEntry.type, stringEntry); // Use editor_id, index, and type as key
		}

		//Update translations in the map only if the editor_id, index, and type exist in both JSON files
		for (const auto& entry : translatedJson) {
			auto it = entries.find(entry["editor_id"].get<std::string>() + "_" + (entry["index"].is_null() ? "null" : std::to_string(entry["index"].get<int>())) + "_" + entry["type"].get<std::string>());
			if (it != entries.end()) {
				it->second.translated = entry["string"];
			}
		}

		//Output merged data only if editor_id, index, and type exist in both original and translated JSON
		json outputJson;
		for (const auto& originalEntry : originalJson) {
			const auto& editor_id = originalEntry["editor_id"].get<std::string>();
			const auto& index = originalEntry["index"].is_null() ? std::optional<int>() : originalEntry["index"].get<int>();
			const auto& type = originalEntry["type"].get<std::string>();

			auto it = entries.find(editor_id + "_" + (index ? std::to_string(*index) : "null") + "_" + type);
			if (it != entries.end() && !it->second.translated.empty()) {
				const StringEntry& mergedEntry = it->second;

				json jsonEntry = {
				{"editor_id", mergedEntry.editor_id},
				{"type", mergedEntry.type},
				{"original", mergedEntry.original},
				{"string", mergedEntry.translated}
				};

				if (mergedEntry.index.has_value()) {
					jsonEntry["index"] = *mergedEntry.index;
				}
				else {
					jsonEntry["index"] = nullptr;
				}

				outputJson.emplace_back(jsonEntry);
			}
		}

		//Save the merged data in output.json
		std::ofstream outputFile("output.json");
		outputFile << outputJson.dump(4); //Save with indentations

		std::cout << "Merge successful. Merged JSON saved to output.json." << std::endl;
	}
	catch (const std::exception& e) {
		std::cerr << "Error: " << e.what() << std::endl;
		return 1;
	}

	return 0;
}

























