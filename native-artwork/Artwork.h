// Required Notice: Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng
// Source-only candidate. This is not an API present in official beta 1.1.5.
#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace awtrix::artwork {

constexpr std::size_t kEncodedLimit = 1024 * 1024;
constexpr std::size_t kDecoderBudget = 6 * 1024 * 1024;
constexpr std::size_t kSourcePixelLimit = 1024 * 1024;
constexpr unsigned kTargetEdgeLimit = 32;

enum class Error { None, BadSize, TooLarge, Unsupported, InvalidImage, NoMemory };
const char* errorName(Error error);

struct Frame {
  unsigned width = 0, height = 0;
  std::vector<std::uint32_t> pixels;  // row-major 0xRRGGBB, alpha over black
};

struct Result {
  Error error = Error::InvalidImage;
  std::shared_ptr<const Frame> frame;
  std::size_t decoderPeakBytes = 0;
};

// Runs in the native image worker, never in draw() or in the Berry interpreter.
// Accepts JPEG (including progressive) and PNG, with a centered crop and area
// resampling. The encoded input remains owned by the caller for this call only.
Result decode(const std::uint8_t* data, std::size_t size, unsigned width, unsigned height);

// A streaming HTTP adapter must append each chunk, not collect an unbounded
// response and check its size afterward. A failure poisons this buffer.
class EncodedBuffer {
 public:
  bool append(const std::uint8_t* data, std::size_t size);
  const std::vector<std::uint8_t>& bytes() const { return bytes_; }
  Error error() const { return error_; }
 private:
  std::vector<std::uint8_t> bytes_;
  Error error_ = Error::None;
};

enum class Decision { Fetch, Cached, Unchanged, Cleared, Rejected };
struct Ticket {
  std::uint64_t generation = 0;
  std::string url;
  unsigned width = 0, height = 0;
};
struct Request {
  Decision decision;
  Ticket ticket;
};

// Main-thread lifecycle coordinator. The worker receives a COPY of the ticket;
// completion is delivered on the main thread. No worker accesses this object.
// Only one decoded frame is cached; encoded bytes are never retained here.
class Session {
 public:
  Request request(const std::string& url, unsigned width, unsigned height);
  bool complete(const Ticket& ticket, Result result);
  void clear();  // also invalidate before destroying/unloading the owning app
  const std::shared_ptr<const Frame>& frame() const { return current_; }
  Error error() const { return error_; }
 private:
  Ticket wanted_;
  Ticket cached_;
  bool pending_ = false;
  Error error_ = Error::None;
  std::shared_ptr<const Frame> current_, cache_;
};

}  // namespace awtrix::artwork
