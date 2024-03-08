#include <iostream>
#include <fstream>
#include <ankerl/unordered_dense.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct StringEntry {
	std::string_view editor_id;
	std::string_view type;
	std::string_view original;
	std::string_view translated;
	std::optional<int> index;
};

size_t hashStringEntry(const StringEntry& entry) {
	size_t hashValue = 0;
	hashValue ^= std::hash<std::string_view>{}(entry.editor_id);
	hashValue ^= std::hash<std::string_view>{}(entry.type);
	if (entry.index.has_value()) {
		hashValue ^= std::hash<int>{}(*entry.index);
	}
	return hashValue;
}

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

		ankerl::unordered_dense::map<size_t, StringEntry> entries;

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

			size_t key = hashStringEntry(stringEntry); //Compute the hash value
			entries.emplace(key, stringEntry); //Use the hash value as key
		}

		//Update translations in the map only if the editor_id, index, and type exist in both JSON files
		for (const auto& entry : translatedJson) {
			StringEntry stringEntry;
			stringEntry.editor_id = entry["editor_id"];
			stringEntry.type = entry["type"];
			stringEntry.translated = entry["string"];
			if (!entry["index"].is_null()) {
				stringEntry.index = entry["index"].get<int>(); // Store as integer
			}

			size_t key = hashStringEntry(stringEntry);
			auto it = entries.find(key);
			if (it != entries.end()) {
				it->second.translated = stringEntry.translated;
			}
		}

		//Output merged data only if editor_id, index, and type exist in both original and translated JSON
		json outputJson;
		for (const auto& originalEntry : originalJson) {

			StringEntry stringEntry;
			stringEntry.editor_id = originalEntry["editor_id"];
			stringEntry.type = originalEntry["type"];
			if (!originalEntry["index"].is_null()) {
				stringEntry.index = originalEntry["index"].get<int>(); //Store as integer
			}

			size_t key = hashStringEntry(stringEntry);
			auto it = entries.find(key);
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