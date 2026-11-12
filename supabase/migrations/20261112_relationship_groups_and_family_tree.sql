-- Peter Nexus: optional relationship fields for contact classification and genealogy.
-- Safe to run repeatedly. Existing contact and node records are preserved.
ALTER TABLE public.contacts
  ADD COLUMN IF NOT EXISTS relationship_group text NOT NULL DEFAULT 'friend',
  ADD COLUMN IF NOT EXISTS family_relation text,
  ADD COLUMN IF NOT EXISTS parent_contact_id uuid REFERENCES public.contacts(id) ON DELETE SET NULL;

ALTER TABLE public.nodes
  ADD COLUMN IF NOT EXISTS relationship_group text,
  ADD COLUMN IF NOT EXISTS family_relation text,
  ADD COLUMN IF NOT EXISTS parent_node_id text;

-- Classify known kinship terms without changing the saved relationship label.
UPDATE public.contacts
SET relationship_group = 'family'
WHERE lower(coalesce(category, '') || ' ' || coalesce(relation_type, '')) ~
  '(famigli|family|padre|madre|genitor|figli|fratell|sorell|nonn|zi[oa]|cugin|nipot|marito|moglie|suocer|cognat)';

UPDATE public.nodes
SET relationship_group = 'family'
WHERE type = 'person'
  AND lower(coalesce(category, '') || ' ' || coalesce(relation_type, '')) ~
  '(famigli|family|padre|madre|genitor|figli|fratell|sorell|nonn|zi[oa]|cugin|nipot|marito|moglie|suocer|cognat)';

CREATE INDEX IF NOT EXISTS contacts_parent_contact_id_idx
  ON public.contacts (parent_contact_id);
CREATE INDEX IF NOT EXISTS nodes_parent_node_id_idx
  ON public.nodes (parent_node_id);

COMMENT ON COLUMN public.contacts.parent_contact_id IS
  'Optional parent contact; set explicitly to represent a known genealogy edge.';
COMMENT ON COLUMN public.nodes.parent_node_id IS
  'Optional parent node id consumed by the Nexus genealogy visualization.';
