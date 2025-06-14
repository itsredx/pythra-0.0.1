#include "framework/reconciler.h"
#include "widgets/concrete_widgets.h"
#include <iostream>
#include <vector>
#include <memory>

// Helper to print patches for demonstration
void print_patches(const std::vector<pythra::Patch>& patches) {
    std::cout << "--- Generated " << patches.size() << " Patches ---" << std::endl;
    for (const auto& patch : patches) {
        std::cout << "Action: ";
        switch (patch.action) {
            case pythra::PatchAction::INSERT: std::cout << "INSERT"; break;
            case pythra::PatchAction::UPDATE: std::cout << "UPDATE"; break;
            case pythra::PatchAction::REMOVE: std::cout << "REMOVE"; break;
            case pythra::PatchAction::MOVE:   std::cout << "MOVE";   break;
        }
        std::cout << ", html_id: " << patch.html_id << std::endl;

        if (patch.action == pythra::PatchAction::INSERT) {
            std::cout << "  - Parent: " << std::any_cast<std::string>(patch.data.at("parent_html_id")) << std::endl;
            std::cout << "  - HTML: " << std::any_cast<std::string>(patch.data.at("html")) << std::endl;
        } else if (patch.action == pythra::PatchAction::UPDATE) {
            // In a real app, you'd inspect the "props" map here
            std::cout << "  - Contains " << patch.data.at("props").type().name() << " changes." << std::endl;
        }
    }
    std::cout << "-------------------------" << std::endl;
}


int main() {
    pythra::Reconciler reconciler;

    // --- State 1: Initial Render ---
    std::cout << "\n>>> SCENE 1: Initial Render <<<" << std::endl;
    auto text_widget1 = std::make_shared<pythra::TextWidget>("Hello World");
    auto root_widget1 = std::make_shared<pythra::ContainerWidget>(std::vector<std::shared_ptr<pythra::Widget>>{text_widget1});

    auto patches1 = reconciler.reconcile_subtree(root_widget1.get(), "root_container");
    print_patches(patches1);


    // --- State 2: Update the Text ---
    std::cout << "\n>>> SCENE 2: Update Text Content <<<" << std::endl;
    // We "rebuild" the widget tree with the new state, as a real framework would.
    text_widget1->set_text("Hello C++!"); // In a real app, you'd create a new widget
    auto root_widget2 = std::make_shared<pythra::ContainerWidget>(std::vector<std::shared_ptr<pythra::Widget>>{text_widget1});

    auto patches2 = reconciler.reconcile_subtree(root_widget2.get(), "root_container");
    print_patches(patches2);


    // --- State 3: Replace the widget ---
    std::cout << "\n>>> SCENE 3: Replace Widget (No Keys) <<<" << std::endl;
    auto text_widget3 = std::make_shared<pythra::TextWidget>("A completely different widget");
    auto root_widget3 = std::make_shared<pythra::ContainerWidget>(std::vector<std::shared_ptr<pythra::Widget>>{text_widget3});

    auto patches3 = reconciler.reconcile_subtree(root_widget3.get(), "root_container");
    print_patches(patches3);


    return 0;
}