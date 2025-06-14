// framework/reconciler.h

#pragma once

#include "widget.h" // Assumed widget interface
#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <variant>
#include <functional>
#include <any>
#include <optional>
#include <set>

namespace pythra {

// --- Patch Definition ---
enum class PatchAction { INSERT, REMOVE, UPDATE, MOVE };

struct Patch {
    PatchAction action;
    std::string html_id;
    PropsMap data; // Using PropsMap for flexible data payload
};

// --- NodeData: Stores info about a rendered widget ---
struct NodeData {
    std::string html_id;
    std::string widget_type;
    std::optional<Key> key;
    std::optional<std::string> internal_id;
    PropsMap props;
    std::string parent_html_id;
    std::vector<WidgetUniqueID> children_keys;
};

// --- ID Generator ---
class IDGenerator {
public:
    IDGenerator() : count_(0) {}
    std::string next_id() {
        return "fw_id_" + std::to_string(++count_);
    }
private:
    long long count_;
};

// --- Custom Hasher for WidgetUniqueID (std::variant) ---
struct WidgetUniqueIDHasher {
    size_t operator()(const WidgetUniqueID& id) const {
        return std::visit([](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, Key>) {
                return std::hash<Key>{}(value);
            } else {
                return std::hash<std::string>{}(value);
            }
        }, id);
    }
};

using RenderedMap = std::unordered_map<WidgetUniqueID, NodeData, WidgetUniqueIDHasher>;
using CssGeneratorFunc = std::function<std::string(const std::any&)>; // Placeholder for CSS generation

class Reconciler {
public:
    Reconciler();

    // Main reconciliation entry point
    std::vector<Patch> reconcile_subtree(Widget* current_subtree_root, const std::string& parent_html_id, const std::string& context_key = "main");

    // Clears state for a specific context
    void clear_context(const std::string& context_key);

    // Public for inspection, e.g., in testing or CSS generation phase
    const std::unordered_map<std::string, std::pair<CssGeneratorFunc, std::any>>& get_active_css_details() const;

private:
    RenderedMap& get_map_for_context(const std::string& context_key);

    // Helper functions mirroring the Python implementation
    static std::string get_widget_render_tag(Widget* widget);
    static std::string generate_html_stub(Widget* widget, const std::string& html_id, const PropsMap& props);
    void add_node_to_map_and_css(Widget* widget, const std::string& html_id, const std::string& parent_html_id, const PropsMap& props, RenderedMap& new_rendered_map);
    static std::optional<PropsMap> diff_props(const PropsMap& old_props, const PropsMap& new_props);

    // Core recursive diffing logic
    void diff_node_recursive(const std::optional<WidgetUniqueID>& old_node_key, Widget* new_widget, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map);
    void insert_node_recursive(Widget* new_widget, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map, const PropsMap* layout_props_override = nullptr, const std::optional<std::string>& before_id = std::nullopt);
    void diff_children_recursive(const std::vector<WidgetUniqueID>& old_children_keys, const std::vector<Widget*>& new_children_widgets, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map);

    std::unordered_map<std::string, RenderedMap> context_maps_;
    IDGenerator id_generator_;
    std::unordered_map<std::string, std::pair<CssGeneratorFunc, std::any>> active_css_details_;
};

} // namespace pythra