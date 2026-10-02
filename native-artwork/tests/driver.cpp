// Required Notice: Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng
#include "Artwork.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <thread>

using namespace awtrix::artwork;

Result sample(unsigned w = 16, unsigned h = 16) {
  auto frame = std::make_shared<Frame>();
  frame->width = w; frame->height = h; frame->pixels.assign(w * h, 0xabcdef);
  return {Error::None, frame, 0};
}
void lifecycleTests() {
  Session session;
  const std::string a = "https://images.example/album-a.jpg";
  const std::string b = "https://images.example/album-b.jpg";
  auto first = session.request(a, 16, 16);
  assert(first.decision == Decision::Fetch);
  assert(session.request(a, 16, 16).decision == Decision::Unchanged);
  auto second = session.request(b, 16, 16);
  assert(!session.complete(first.ticket, sample())); // stale album never wins
  assert(session.complete(second.ticket, sample()));
  assert(session.frame()->pixels[0] == 0xabcdef);
  assert(!session.complete(second.ticket, sample())); // duplicate callback
  assert(session.request(b, 16, 16).decision == Decision::Unchanged);
  auto third = session.request(a, 16, 16);
  assert(!session.frame()); // don't show B under A's title during fetch
  assert(session.request(b, 16, 16).decision == Decision::Cached);
  assert(!session.complete(third.ticket, sample()));
  auto resized = session.request(b, 10, 10);
  assert(resized.decision == Decision::Fetch);
  assert(session.complete(resized.ticket, sample(16, 16)));
  assert(!session.frame()); // wrong-size result must fall back
  auto retry = session.request(b, 10, 10);
  assert(retry.decision == Decision::Fetch);
  assert(session.complete(retry.ticket, sample(10, 10)));
  assert(session.frame()->pixels.size() == 100);
  auto lost = session.request(a, 16, 16);
  session.clear(); // unload invalidates in-flight callbacks and frees cache
  assert(!session.frame());
  assert(!session.complete(lost.ticket, sample()));
  assert(session.request("", 16, 16).decision == Decision::Cleared);
  for (const auto& bad : {"file:///etc/passwd", "https://user:secret@images.example/x", "https://", "ftp://images.example/x", "https://images.example/\nsecret"}) {
    assert(session.request(bad, 16, 16).decision == Decision::Rejected);
    assert(!session.frame());
  }
  assert(session.request(a, 0, 16).decision == Decision::Rejected);
  assert(session.request(a, 33, 16).decision == Decision::Rejected);
  auto error = session.request(a, 16, 16);
  assert(session.complete(error.ticket, {Error::InvalidImage, {}, 0}));
  assert(!session.frame());
  assert(session.request(a, 16, 16).decision == Decision::Fetch);
  EncodedBuffer chunks;
  std::vector<std::uint8_t> bytes(kEncodedLimit, 0);
  assert(chunks.append(bytes.data(), kEncodedLimit - 1));
  assert(chunks.append(bytes.data(), 1));
  assert(!chunks.append(bytes.data(), 1));
  assert(chunks.error() == Error::TooLarge);
  assert(!chunks.append(bytes.data(), 0));
  assert(chunks.bytes().size() == kEncodedLimit);
  EncodedBuffer malformed;
  assert(!malformed.append(nullptr, 1));
  EncodedBuffer empty;
  assert(empty.append(nullptr, 0));
  std::cout << "lifecycle and stream tests passed\n";
}

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--self-test") { lifecycleTests(); return 0; }
  if (argc != 4) return 2;
  unsigned w = static_cast<unsigned>(std::stoul(argv[2]));
  unsigned h = static_cast<unsigned>(std::stoul(argv[3]));
  std::ifstream file(argv[1], std::ios::binary);
  std::vector<std::uint8_t> data((std::istreambuf_iterator<char>(file)), {});
  auto result = decode(data.data(), data.size(), w, h);
  // Exercise the decoder's thread-local allocator on independent jobs too.
  std::thread other([&] {
    auto again = decode(data.data(), data.size(), w, h);
    assert(again.error == result.error);
    if (again.frame) assert(again.frame->pixels == result.frame->pixels);
  });
  other.join();
  std::cout << "{\"error\":\"" << errorName(result.error)
            << "\",\"decoder_peak_bytes\":" << result.decoderPeakBytes;
  if (result.frame) {
    std::cout << ",\"width\":" << result.frame->width << ",\"height\":" << result.frame->height << ",\"pixels\":[";
    bool first = true;
    for (auto pixel : result.frame->pixels) { if (!first) std::cout << ','; first = false; std::cout << pixel; }
    std::cout << ']';
  }
  std::cout << "}\n";
}
