// framework/widget.h

#pragma once

#include <string>
#include <vector>
#include <any>
#include <variant>
#include <optional>
#include <unordered_map>
#include <utility>

namespace pythra {

// A simplified, hashable Key class. In a real scenario, this could be a variant.
class Key {
public:
    explicit Key(std::string value) : value_(std::move(value)) {}
    bool operator==(const Key& other) const { return value_ == other.value_; }
    [[nodiscard]] const std::string& value() const { return value_; }

private:
    std::string value_;
};

} // namespace pythra

// Custom hash for pythra::Key
namespace std {
template <>
struct hash<pythra::Key> {
    size_t operator()(const pythra::Key& k) const {
        return hash<string>()(k.value());
    }
};
} // namespace std

namespace pythra {

// Type aliases for clarity
using WidgetUniqueID = std::variant<Key, std::string>;
using PropsMap = std::unordered_map<std::string, std::any>;

// Forward declaration
class Widget;

// Mock interface for what the Reconciler expects from a Widget.
class Widget {
public:
    virtual ~Widget() = default;

    [[nodiscard]] virtual std::string get_type_name() const = 0;
    [[nodiscard]] virtual WidgetUniqueID get_unique_id() const = 0;
    [[nodiscard]] virtual std::vector<Widget*> get_children() const = 0;
    [[nodiscard]] virtual PropsMap render_props() const = 0;
    [[nodiscard]] virtual std::optional<Key> get_key() const = 0;
    [[nodiscard]] virtual std::optional<std::string> get_internal_id() const = 0;
};

} // namespace pythra