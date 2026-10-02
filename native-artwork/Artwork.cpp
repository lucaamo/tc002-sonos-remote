// Required Notice: Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng
#include "Artwork.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <new>

namespace {
struct Budget { std::size_t used = 0, peak = 0; bool refused = false; };
thread_local Budget* activeBudget = nullptr;
struct alignas(std::max_align_t) Allocation { std::size_t size; };

void* imageMalloc(std::size_t size) {
  if (!activeBudget) return nullptr;
  if (size > awtrix::artwork::kDecoderBudget - activeBudget->used ||
      size > std::numeric_limits<std::size_t>::max() - sizeof(Allocation)) {
    activeBudget->refused = true; return nullptr;
  }
  auto* block = static_cast<Allocation*>(std::malloc(sizeof(Allocation) + size));
  if (!block) { activeBudget->refused = true; return nullptr; }
  block->size = size;
  activeBudget->used += size;
  activeBudget->peak = std::max(activeBudget->peak, activeBudget->used);
  return block + 1;
}
void imageFree(void* ptr) {
  if (!ptr) return;
  auto* block = static_cast<Allocation*>(ptr) - 1;
  activeBudget->used -= block->size;
  std::free(block);
}
void* imageRealloc(void* ptr, std::size_t size) {
  if (!ptr) return imageMalloc(size);
  const auto previous = (static_cast<Allocation*>(ptr) - 1)->size;
  // Count both blocks while reallocating so peak memory is bounded as well.
  void* next = imageMalloc(size);
  if (!next) return nullptr;
  std::memcpy(next, ptr, std::min(previous, size));
  imageFree(ptr);
  return next;
}
struct BudgetScope {
  Budget budget;
  BudgetScope() { activeBudget = &budget; }
  ~BudgetScope() { activeBudget = nullptr; }
};
}  // namespace

#define STBI_ONLY_JPEG
#define STBI_ONLY_PNG
#define STBI_NO_STDIO
#define STBI_NO_HDR
#define STBI_NO_LINEAR
#define STBI_MAX_DIMENSIONS 2048
#define STBI_MALLOC imageMalloc
#define STBI_REALLOC imageRealloc
#define STBI_FREE imageFree
#define STB_IMAGE_IMPLEMENTATION
#include "vendor/stb_image.h"

namespace awtrix::artwork {

const char* errorName(Error error) {
  switch (error) {
    case Error::None: return "ok";
    case Error::BadSize: return "bad_size";
    case Error::TooLarge: return "too_large";
    case Error::Unsupported: return "unsupported";
    case Error::InvalidImage: return "invalid_image";
    case Error::NoMemory: return "no_memory";
  }
  return "invalid_image";
}

Result decode(const std::uint8_t* data, std::size_t size, unsigned width, unsigned height) {
  Result out;
  if (!width || !height || width > kTargetEdgeLimit || height > kTargetEdgeLimit) {
    out.error = Error::BadSize; return out;
  }
  if (size > kEncodedLimit) { out.error = Error::TooLarge; return out; }
  if (!data || size < 8) return out;
  const bool jpeg = data[0] == 0xff && data[1] == 0xd8;
  const std::uint8_t pngMagic[] = {137, 80, 78, 71, 13, 10, 26, 10};
  const bool png = std::memcmp(data, pngMagic, 8) == 0;
  if (!jpeg && !png) { out.error = Error::Unsupported; return out; }

  BudgetScope scope;
  int sw = 0, sh = 0, channels = 0;
  if (!stbi_info_from_memory(data, static_cast<int>(size), &sw, &sh, &channels)) return out;
  if (sw <= 0 || sh <= 0 || sw > 2048 || sh > 2048 ||
      static_cast<std::size_t>(sw) * sh > kSourcePixelLimit) {
    out.error = Error::TooLarge; return out;
  }
  // All decoder allocations go through the per-thread bounded allocator.
  std::unique_ptr<stbi_uc, decltype(&imageFree)> rgba(
      stbi_load_from_memory(data, static_cast<int>(size), &sw, &sh, &channels, 4), imageFree);
  out.decoderPeakBytes = scope.budget.peak;
  if (!rgba) {
    out.error = scope.budget.refused ? Error::NoMemory : Error::InvalidImage;
    return out;
  }
  try {
    auto frame = std::make_shared<Frame>();
    frame->width = width; frame->height = height;
    frame->pixels.resize(static_cast<std::size_t>(width) * height);
    // Match target aspect ratio without stretching the album. Average each
    // target pixel's footprint: tiny covers keep colors without aliasing.
    const double scale = std::min(static_cast<double>(sw) / width,
                                  static_cast<double>(sh) / height);
    const double left = (sw - width * scale) / 2;
    const double top = (sh - height * scale) / 2;
    for (unsigned y = 0; y < height; ++y) for (unsigned x = 0; x < width; ++x) {
      const double x0 = left + x * scale, x1 = x0 + scale;
      const double y0 = top + y * scale, y1 = y0 + scale;
      double sums[3] = {0, 0, 0}, weight = 0;
      for (int sy = std::max(0, static_cast<int>(std::floor(y0)));
           sy < std::min(sh, static_cast<int>(std::ceil(y1))); ++sy) {
        const double wy = std::max(0.0, std::min(y1, sy + 1.0) - std::max(y0, double(sy)));
        for (int sx = std::max(0, static_cast<int>(std::floor(x0)));
             sx < std::min(sw, static_cast<int>(std::ceil(x1))); ++sx) {
          const double w = wy * std::max(0.0, std::min(x1, sx + 1.0) - std::max(x0, double(sx)));
          const auto* p = rgba.get() + (static_cast<std::size_t>(sy) * sw + sx) * 4;
          for (int c = 0; c < 3; ++c) sums[c] += w * p[c] * (p[3] / 255.0);
          weight += w;
        }
      }
      std::uint32_t color = 0;
      for (double sum : sums) {
        const auto channel = static_cast<unsigned>(std::clamp(std::lround(sum / weight), 0L, 255L));
        color = (color << 8) | channel;
      }
      frame->pixels[y * width + x] = color;
    }
    out.error = Error::None; out.frame = std::move(frame);
  } catch (const std::bad_alloc&) { out.error = Error::NoMemory; }
  return out;
}

bool EncodedBuffer::append(const std::uint8_t* data, std::size_t size) {
  if (error_ != Error::None) return false;
  if (size > kEncodedLimit - bytes_.size()) { error_ = Error::TooLarge; return false; }
  if (!size) return true;
  if (!data) { error_ = Error::InvalidImage; return false; }
  try {
    if (!bytes_.capacity()) bytes_.reserve(kEncodedLimit);
    bytes_.insert(bytes_.end(), data, data + size);
  }
  catch (const std::bad_alloc&) { error_ = Error::NoMemory; return false; }
  return true;
}

namespace {
bool sameImage(const Ticket& a, const Ticket& b) {
  return a.url == b.url && a.width == b.width && a.height == b.height;
}
bool safeUrl(const std::string& url) {
  if (url.size() > 4096 || url.find_first_of("\r\n\t ") != std::string::npos ||
      url.find('\0') != std::string::npos) return false;
  const auto start = url.rfind("https://", 0) == 0 ? 8u : (url.rfind("http://", 0) == 0 ? 7u : 0u);
  if (!start) return false;
  const auto end = url.find_first_of("/?#", start);
  const auto authority = url.substr(start, end == std::string::npos ? end : end - start);
  return !authority.empty() && authority.find('@') == std::string::npos;
}
}

Request Session::request(const std::string& url, unsigned width, unsigned height) {
  Ticket next{wanted_.generation + 1, url, width, height};
  if (url.empty()) { clear(); return {Decision::Cleared, wanted_}; }
  if (!safeUrl(url) || !width || !height || width > kTargetEdgeLimit || height > kTargetEdgeLimit) {
    clear(); error_ = Error::BadSize; return {Decision::Rejected, wanted_};
  }
  if (sameImage(next, wanted_) && (pending_ || current_)) return {Decision::Unchanged, wanted_};
  wanted_ = next;
  current_.reset(); pending_ = false; error_ = Error::None;
  if (cache_ && sameImage(next, cached_)) {
    current_ = cache_; return {Decision::Cached, wanted_};
  }
  pending_ = true;
  return {Decision::Fetch, wanted_};
}

bool Session::complete(const Ticket& ticket, Result result) {
  if (!pending_ || ticket.generation != wanted_.generation || !sameImage(ticket, wanted_)) return false;
  pending_ = false;
  error_ = result.error;
  if (result.error != Error::None || !result.frame ||
      result.frame->width != ticket.width || result.frame->height != ticket.height ||
      result.frame->pixels.size() != static_cast<std::size_t>(ticket.width) * ticket.height) {
    if (error_ == Error::None) error_ = Error::InvalidImage;
    current_.reset(); return true;
  }
  current_ = std::move(result.frame); cache_ = current_; cached_ = ticket;
  return true;
}

void Session::clear() {
  ++wanted_.generation;
  wanted_.url.clear(); wanted_.width = wanted_.height = 0;
  pending_ = false; error_ = Error::None;
  current_.reset(); cache_.reset(); cached_ = {};
}
}  // namespace awtrix::artwork
