from enum import Enum
from typing import Optional, Self, Union
from pydantic import BaseModel, Field

from llama_index.schema import NodeWithScore

class SynthesisMode(str, Enum):
    """How result nodes should be synthesized into a single result."""

    REFINE = "refine"
    """
    Refine is an iterative way of generating a response.
    We first use the context in the first node, along with the query, to generate an \
    initial answer.
    We then pass this answer, the query, and the context of the second node as input \
    into a “refine prompt” to generate a refined answer. We refine through N-1 nodes, \
    where N is the total number of nodes.
    """

    COMPACT = "compact"
    """
    Compact and refine mode first combine text chunks into larger consolidated chunks \
    that more fully utilize the available context window, then refine answers \
    across them.
    This mode is faster than refine since we make fewer calls to the LLM.
    """

    SIMPLE_SUMMARIZE = "simple_summarize"
    """
    Merge all text chunks into one, and make a LLM call.
    This will fail if the merged text chunk exceeds the context window size.
    """

    TREE_SUMMARIZE = "tree_summarize"
    """
    Build a tree index over the set of candidate nodes, with a summary prompt seeded \
    with the query.
    The tree is built in a bottoms-up fashion, and in the end the root node is \
    returned as the response
    """

    GENERATION = "generation"
    """Ignore context, just use LLM to generate a response."""

    NO_TEXT = "no_text"
    """Return the retrieved context nodes, without synthesizing a final response."""

    ACCUMULATE = "accumulate"
    """Synthesize a response for each text chunk, and then return the concatenation."""

    COMPACT_ACCUMULATE = "compact_accumulate"
    """
    Compact and accumulate mode first combine text chunks into larger consolidated \
    chunks that more fully utilize the available context window, then accumulate \
    answers for each of them and finally return the concatenation.
    This mode is faster than accumulate since we make fewer calls to the LLM.
    """

class RetrieveRequest(BaseModel):
    """A request for retrieving unstructured (document) results."""

    query: str
    """The query string to use for retrieval."""

    n: int = 10
    """The number of chunks to retrieve."""

    synthesis_mode: SynthesisMode = SynthesisMode.NO_TEXT
    """Whether to generate a summary of the retrieved results.

    The default (`NO_TEXT`) will disable synthesis.
    """

class TextContent(BaseModel):
    text: str = Field(default="", description="Text content of the node.")
    start_char_idx: Optional[int] = Field(
        default=None, description="Start char index of the node."
    )
    end_char_idx: Optional[int] = Field(
        default=None, description="End char index of the node."
    )

class ImageContent(BaseModel):
    text: Optional[str] = Field(..., description="Textual description of the image.")
    image: Optional[str] = Field(..., description="Image of the node.")
    image_mimetype: Optional[str] = Field(..., description="Mimetype of the image.")
    image_path: Optional[str] = Field(..., description="Path of the image.")
    image_url: Optional[str] = Field(..., description="URL of the image.")

class Chunk(BaseModel):
    """A retrieved chunk."""
    content: Union[TextContent, ImageContent]
    score: Optional[float] = None

    @staticmethod
    def from_llama_index(node: NodeWithScore) -> Self:
        score = node.score

        content = None
        from llama_index.schema import TextNode, ImageNode
        if isinstance(node.node, TextNode):
            content = TextContent(
                text = node.node.text,
                start_char_idx = node.node.start_char_idx,
                end_char_idx = node.node.end_char_idx
            )
        elif isinstance(node.node, ImageNode):
            content = ImageContent(
                text = node.node.text if node.node.text else None,
                image = node.node.image,
                image_mimetype = node.node.image_mimetype,
                image_path = node.node.image_path,
                image_url = node.node.image_url,
            )
        else:
            raise NotImplementedError(f"Unsupported node type ({node.node.class_name()}): {node!r}")

        return Chunk(content=content, score=score)