// framework/reconciler.cpp

#include "reconciler.h"
#include <set>
#include <algorithm>
#include <sstream>

namespace pythra {

// --- Helper Functions ---

// Simple HTML escape function
std::string html_escape(const std::string& data) {
    std::string buffer;
    buffer.reserve(data.size());
    for(char c : data) {
        switch(c) {
            case '&':  buffer.append("&");       break;
            case '\"': buffer.append(""");      break;
            case '\'': buffer.append("'");      break;
            case '<':  buffer.append("<");        break;
            case '>':  buffer.append(">");        break;
            default:   buffer.push_back(c);         break;
        }
    }
    return buffer;
}

// Helper to safely get a property from the PropsMap
template<typename T>
T get_prop(const PropsMap& props, const std::string& key, T default_value) {
    auto it = props.find(key);
    if (it != props.end()) {
        try {
            return std::any_cast<T>(it->second);
        } catch (const std::bad_any_cast&) {
            // In a real app, log this error
        }
    }
    return default_value;
}


// --- Reconciler Implementation ---

Reconciler::Reconciler() {
    std::cout << "Reconciler Initialized" << std::endl;
}

const std::unordered_map<std::string, std::pair<CssGeneratorFunc, std::any>>& Reconciler::get_active_css_details() const {
    return active_css_details_;
}

RenderedMap& Reconciler::get_map_for_context(const std::string& context_key) {
    // .try_emplace creates the map if it doesn't exist, otherwise returns the existing one.
    return context_maps_.try_emplace(context_key).first->second;
}

void Reconciler::clear_context(const std::string& context_key) {
    if (context_maps_.erase(context_key) > 0) {
        std::cout << "Reconciler context '" << context_key << "' cleared." << std::endl;
    }
}

std::vector<Patch> Reconciler::reconcile_subtree(Widget* current_subtree_root, const std::string& parent_html_id, const std::string& context_key) {
    std::cout << "\n--- Reconciling Subtree (Context: '" << context_key << "', Target Parent ID: '" << parent_html_id << "') ---" << std::endl;

    std::vector<Patch> patches;
    RenderedMap new_rendered_map;
    const RenderedMap& previous_map = get_map_for_context(context_key);

    if (context_key == "main") {
        active_css_details_.clear();
    }

    std::optional<WidgetUniqueID> old_root_key;
    for (const auto& [key, data] : previous_map) {
        if (data.parent_html_id == parent_html_id) {
            old_root_key = key;
            break;
        }
    }
    // Handle edge case where the root is the only element
    if (!old_root_key && previous_map.size() == 1 && current_subtree_root) {
        const auto& [single_old_key, single_old_data] = *previous_map.begin();
         if (current_subtree_root->get_unique_id() == single_old_key || 
             (single_old_data.key.has_value() == current_subtree_root->get_key().has_value() && single_old_data.widget_type == current_subtree_root->get_type_name())) {
             old_root_key = single_old_key;
         }
    }

    diff_node_recursive(old_root_key, current_subtree_root, parent_html_id, patches, new_rendered_map, previous_map);

    // --- Find and remove stale nodes ---
    for (const auto& [old_key, old_data] : previous_map) {
        if (new_rendered_map.find(old_key) == new_rendered_map.end()) {
            patches.push_back({PatchAction::REMOVE, old_data.html_id, {}});
        }
    }

    context_maps_[context_key] = std::move(new_rendered_map);
    return patches;
}


void Reconciler::diff_node_recursive(const std::optional<WidgetUniqueID>& old_node_key, Widget* new_widget, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map) {
    // In C++, layout widgets are handled by their parent or by composition.
    // This logic is simplified; a full implementation would involve passing layout hints down.
    // For this conversion, we assume the widget passed is the one to be rendered.
    if (!new_widget && !old_node_key.has_value()) {
        return;
    }
    
    // Node removal is handled at the end of reconcile_subtree. If new_widget is null, there's nothing to update or insert.
    if (!new_widget) {
        return;
    }
    
    auto old_data_it = old_node_key ? previous_map.find(*old_node_key) : previous_map.end();

    if (old_data_it == previous_map.end()) {
        // --- INSERT case ---
        insert_node_recursive(new_widget, parent_html_id, patches, new_rendered_map, previous_map);
        return;
    }
    
    // --- UPDATE/REPLACE case ---
    const NodeData& old_data = old_data_it->second;
    const std::string& new_type = new_widget->get_type_name();
    const auto& new_key = new_widget->get_key();

    bool should_replace = (new_key.has_value() && old_data.key != new_key) ||
                          (old_data.key.has_value() && !new_key.has_value()) ||
                          (!new_key.has_value() && !old_data.key.has_value() && old_data.widget_type != new_type) ||
                          (new_key.has_value() && old_data.key.has_value() && *old_data.key == *new_key && old_data.widget_type != new_type);

    if (should_replace) {
        insert_node_recursive(new_widget, parent_html_id, patches, new_rendered_map, previous_map);
        // The old node will be garbage collected as a REMOVE patch at the end.
        return;
    }

    // --- UPDATE in-place ---
    const std::string& html_id = old_data.html_id;
    PropsMap new_props = new_widget->render_props();
    
    // Note: CSS details collection for updated nodes would happen here
    // add_node_to_map_and_css(...);
    
    auto prop_changes = diff_props(old_data.props, new_props);
    if (prop_changes) {
        patches.push_back({PatchAction::UPDATE, html_id, {{"props", *prop_changes}}});
    }

    std::vector<WidgetUniqueID> children_keys;
    for(auto* child : new_widget->get_children()){
        children_keys.push_back(child->get_unique_id());
    }

    new_rendered_map[new_widget->get_unique_id()] = {
        html_id, new_type, new_key,
        new_widget->get_internal_id(),
        std::move(new_props), parent_html_id,
        std::move(children_keys)
    };

    diff_children_recursive(
        old_data.children_keys, new_widget->get_children(),
        html_id, patches, new_rendered_map, previous_map
    );
}


void Reconciler::insert_node_recursive(Widget* new_widget, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map, const PropsMap* layout_props_override, const std::optional<std::string>& before_id) {
    if (!new_widget) return;

    std::string html_id = id_generator_.next_id();
    PropsMap widget_props = new_widget->render_props();
    if(layout_props_override) {
        widget_props["layout_override"] = *layout_props_override;
    }

    add_node_to_map_and_css(new_widget, html_id, parent_html_id, widget_props, new_rendered_map);

    PropsMap patch_data;
    patch_data["html"] = generate_html_stub(new_widget, html_id, widget_props);
    patch_data["parent_html_id"] = parent_html_id;
    patch_data["props"] = widget_props;
    if (before_id) {
        patch_data["before_id"] = *before_id;
    }
    patches.push_back({PatchAction::INSERT, html_id, std::move(patch_data)});

    // Recursively insert children
    for (Widget* child_widget : new_widget->get_children()) {
        // Children are always new since their parent is new.
        insert_node_recursive(child_widget, html_id, patches, new_rendered_map, previous_map);
    }
}


void Reconciler::diff_children_recursive(const std::vector<WidgetUniqueID>& old_children_keys, const std::vector<Widget*>& new_children_widgets, const std::string& parent_html_id, std::vector<Patch>& patches, RenderedMap& new_rendered_map, const RenderedMap& previous_map) {
    if (old_children_keys.empty() && new_children_widgets.empty()) {
        return;
    }

    std::unordered_map<WidgetUniqueID, size_t, WidgetUniqueIDHasher> old_key_to_index;
    for(size_t i = 0; i < old_children_keys.size(); ++i) {
        old_key_to_index[old_children_keys[i]] = i;
    }
    
    struct ChildInfo {
        WidgetUniqueID key;
        Widget* widget;
        size_t new_idx;
        std::optional<size_t> old_idx;
        std::optional<std::string> html_id;
        bool moved = false;
        bool is_new = false;
    };

    std::vector<ChildInfo> new_children_info;
    new_children_info.reserve(new_children_widgets.size());
    
    long last_matched_old_idx = -1;

    // Pass 1: Match existing nodes and identify moves
    for (size_t i = 0; i < new_children_widgets.size(); ++i) {
        Widget* new_widget = new_children_widgets[i];
        WidgetUniqueID new_key = new_widget->get_unique_id();
        auto it = old_key_to_index.find(new_key);
        
        ChildInfo info{new_key, new_widget, i, std::nullopt, std::nullopt};

        if (it != old_key_to_index.end()) {
            info.old_idx = it->second;
            auto old_data_it = previous_map.find(new_key);
            if (old_data_it != previous_map.end() && old_data_it->second.parent_html_id == parent_html_id) {
                diff_node_recursive(new_key, new_widget, parent_html_id, patches, new_rendered_map, previous_map);
                
                // Retrieve html_id from the potentially updated map
                if(auto new_map_it = new_rendered_map.find(new_key); new_map_it != new_rendered_map.end()) {
                    info.html_id = new_map_it->second.html_id;
                }

                if (static_cast<long>(*info.old_idx) < last_matched_old_idx) {
                    info.moved = true;
                } else {
                    last_matched_old_idx = *info.old_idx;
                }
            } else {
                info.is_new = true;
            }
        } else {
            info.is_new = true;
        }
        new_children_info.push_back(std::move(info));
    }
    
    // Pass 2: Insert new nodes and move existing ones
    for (size_t i = 0; i < new_children_info.size(); ++i) {
        auto& node_info = new_children_info[i];
        
        // Find the html_id of the next stable (not new, not moved) sibling
        std::optional<std::string> before_id;
        for (size_t j = i + 1; j < new_children_info.size(); ++j) {
            const auto& next_node = new_children_info[j];
            if (!next_node.is_new && !next_node.moved && next_node.html_id.has_value()) {
                before_id = next_node.html_id;
                break;
            }
        }

        if (node_info.is_new) {
            insert_node_recursive(node_info.widget, parent_html_id, patches, new_rendered_map, previous_map, nullptr, before_id);
        } else if (node_info.moved && node_info.html_id) {
            PropsMap move_data;
            move_data["parent_html_id"] = parent_html_id;
            if (before_id) move_data["before_id"] = *before_id;
            patches.push_back({PatchAction::MOVE, *node_info.html_id, std::move(move_data)});
        }
    }
    // Note: Removals are handled globally in `reconcile_subtree` by key comparison.
}

// --- Static Helpers on Reconciler ---

std::string Reconciler::get_widget_render_tag(Widget* widget) {
    if (!widget) return "div";
    const std::string& type_name = widget->get_type_name();
    
    static const std::unordered_map<std::string, std::string> tag_map = {
        {"Text", "p"}, {"Image", "img"}, {"Icon", "i"},
        {"TextButton", "button"}, {"ElevatedButton", "button"}, {"IconButton", "button"},
        {"FloatingActionButton", "button"}, {"SnackBarAction", "button"},
        {"ListTile", "div"}, {"Divider", "div"}, {"Dialog", "div"},
    };

    if (type_name == "Icon" && get_prop<bool>(widget->render_props(), "custom_icon_source", false)) {
        return "img";
    }

    auto it = tag_map.find(type_name);
    return (it != tag_map.end()) ? it->second : "div";
}

std::string Reconciler::generate_html_stub(Widget* widget, const std::string& html_id, const PropsMap& props) {
    if (!widget) return "";

    std::string tag = get_widget_render_tag(widget);
    std::string classes = get_prop<std::string>(props, "css_class", "");
    const std::string& type_name = widget->get_type_name();
    std::stringstream attrs;
    std::string inner_html;

    // Attribute generation
    if (type_name == "TextButton" || type_name == "ElevatedButton" || type_name == "IconButton" || type_name == "FloatingActionButton" || type_name == "SnackBarAction") {
        std::string cb_name = get_prop<std::string>(props, "onPressedName", "");
        if (!cb_name.empty()) {
            // Basic escaping for single quotes
            std::replace(cb_name.begin(), cb_name.end(), '\'', ' ');
            attrs << " onclick=\"handleClick('" << cb_name << "')\"";
        }
        std::string tooltip = get_prop<std::string>(props, "tooltip", "");
        if (!tooltip.empty()) attrs << " title=\"" << html_escape(tooltip) << "\"";
    } else if (type_name == "Image") {
        attrs << " src=\"" << html_escape(get_prop<std::string>(props, "src", "")) << "\" alt=\"\"";
    } else if (type_name == "Icon") {
        if(get_prop<std::string>(props, "render_type", "") == "img") {
            attrs << " src=\"" << html_escape(get_prop<std::string>(props, "custom_icon_src", "")) << "\" alt=\"\"";
        } else {
            classes = "fa fa-" + get_prop<std::string>(props, "icon_name", "question-circle") + " " + classes;
        }
    } // ... add other widget types as needed

    // Inner HTML generation for simple widgets
    if (type_name == "Text") {
        inner_html = html_escape(get_prop<std::string>(props, "data", ""));
    } else if (type_name == "TextButton" || type_name == "ElevatedButton") {
        auto children = widget->get_children();
        if(!children.empty() && children[0]){
             // Recursively generate stub for the *first direct child*
             inner_html = generate_html_stub(children[0], html_id + "_child_stub", children[0]->render_props());
        }
    }
    
    std::stringstream ss;
    ss << '<' << tag << " id=\"" << html_id << "\" class=\"" << classes << "\"" << attrs.str();
    if (tag == "img" || tag == "hr" || tag == "br") {
        ss << '>';
    } else {
        ss << '>' << inner_html << "</" << tag << '>';
    }
    return ss.str();
}

void Reconciler::add_node_to_map_and_css(Widget* widget, const std::string& html_id, const std::string& parent_html_id, const PropsMap& props, RenderedMap& new_rendered_map) {
    // CSS generation logic would be implemented here if function pointers were fully defined.
    // For now, it's a placeholder.
    // std::string css_class = get_prop<std::string>(props, "css_class", "");
    // if (!css_class.empty() && active_css_details_.find(css_class) == active_css_details_.end()){
    //      // ... store CSS generation details
    // }

    std::vector<WidgetUniqueID> children_keys;
    for(auto* child : widget->get_children()) {
        children_keys.push_back(child->get_unique_id());
    }
    
    new_rendered_map[widget->get_unique_id()] = {
        html_id,
        widget->get_type_name(),
        widget->get_key(),
        widget->get_internal_id(),
        props,
        parent_html_id,
        std::move(children_keys)
    };
}

std::optional<PropsMap> Reconciler::diff_props(const PropsMap& old_props, const PropsMap& new_props) {
    PropsMap changes;
    std::set<std::string> all_keys;
    for(const auto& [key, val] : old_props) all_keys.insert(key);
    for(const auto& [key, val] : new_props) all_keys.insert(key);

    for (const auto& key : all_keys) {
        auto old_it = old_props.find(key);
        auto new_it = new_props.find(key);

        bool changed = false;
        if (old_it == old_props.end() || new_it == new_props.end()) {
             changed = true; // Key added or removed
        } else {
             // std::any comparison is tricky. A robust solution needs type-aware comparison.
             // For simplicity, we assume if types match, we can compare. Here, we'll just check for non-equality if they have the same type.
             // A real implementation would need a more sophisticated comparison logic.
             if (old_it->second.type() != new_it->second.type()){
                 changed = true;
             } else {
                // This is a simplified check. It only works for basic, comparable types stored in std::any.
                // E.g., comparing two std::vector<int> stored in std::any won't work this way.
                // if (std::any_cast<...>(old_it->second) != std::any_cast<...>(new_it->second))
                // For this example, we'll assume a change if keys are different, which is not ideal but demonstrates the structure.
                // A better way would be to serialize both to string and compare, or have a type-erased equality operator.
             }
        }
        // A placeholder for a real diff: assume if a key exists in new_props, we check for changes.
        if(new_it != new_props.end()) {
            if (old_it == old_props.end()) { // new prop
                 changes[key] = new_it->second;
            } else {
                // Simplified: if a value could be string, we compare.
                if(new_it->second.type() == typeid(std::string) && old_it->second.type() == typeid(std::string)){
                    if(std::any_cast<std::string>(new_it->second) != std::any_cast<std::string>(old_it->second)) {
                        changes[key] = new_it->second;
                    }
                } else if(new_it->second.type() == typeid(bool) && old_it->second.type() == typeid(bool)){
                     if(std::any_cast<bool>(new_it->second) != std::any_cast<bool>(old_it->second)) {
                        changes[key] = new_it->second;
                    }
                }
                // etc. for other types...
            }
        }
    }

    return changes.empty() ? std::nullopt : std::optional<PropsMap>(changes);
}

} // namespace pythra