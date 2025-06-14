#pragma once

#include "../framework/widget.h"
#include <string>
#include <vector>
#include <memory>

namespace pythra {

// A simple container to hold other widgets
class ContainerWidget : public Widget {
public:
    explicit ContainerWidget(std::vector<std::shared_ptr<Widget>> children, std::optional<Key> key = std::nullopt)
        : children_(std::move(children)), key_(std::move(key)) {
        // In a real app, generate a more stable unique ID
        internal_id_ = "container_" + std::to_string(reinterpret_cast<uintptr_t>(this));
    }

    std::string get_type_name() const override { return "Container"; }
    
    WidgetUniqueID get_unique_id() const override {
        if (key_) return *key_;
        return internal_id_;
    }

    std::vector<Widget*> get_children() const override {
        std::vector<Widget*> child_ptrs;
        for (const auto& child : children_) {
            child_ptrs.push_back(child.get());
        }
        return child_ptrs;
    }

    PropsMap render_props() const override { return {}; }
    std::optional<Key> get_key() const override { return key_; }
    std::optional<std::string> get_internal_id() const override { return internal_id_; }

private:
    std::vector<std::shared_ptr<Widget>> children_;
    std::optional<Key> key_;
    std::string internal_id_;
};


class TextWidget : public Widget {
public:
    explicit TextWidget(std::string text, std::optional<Key> key = std::nullopt)
        : text_(std::move(text)), key_(std::move(key)) {
        internal_id_ = "text_" + std::to_string(reinterpret_cast<uintptr_t>(this));
    }

    void set_text(std::string new_text) { text_ = std::move(new_text); }
    
    std::string get_type_name() const override { return "Text"; }
    
    WidgetUniqueID get_unique_id() const override {
        if (key_) return *key_;
        return internal_id_;
    }
    
    std::vector<Widget*> get_children() const override { return {}; } // Text has no children
    
    PropsMap render_props() const override {
        PropsMap props;
        props["data"] = text_;
        return props;
    }
    
    std::optional<Key> get_key() const override { return key_; }
    std::optional<std::string> get_internal_id() const override { return internal_id_; }

private:
    std::string text_;
    std::optional<Key> key_;
    std::string internal_id_;
};

} // namespace pythra